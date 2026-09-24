import base64
import hmac
import json
import logging
import os
import secrets
import time
from collections import deque
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("zeaz-license-server")

app = FastAPI(title="ZeaZ License Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://zmovie.zeaz.dev", "https://license.zeaz.dev"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

# --- Activation rate limiting (stdlib sliding window, per client IP) ---
RATE_LIMIT_MAX = int(os.getenv("LICENSE_RATE_LIMIT_MAX", "20"))
RATE_LIMIT_WINDOW = int(os.getenv("LICENSE_RATE_LIMIT_WINDOW", "60"))
_rate_buckets: dict[str, deque] = {}


def _rate_limited(client_ip: str) -> bool:
    now = time.time()
    bucket = _rate_buckets.setdefault(client_ip, deque())
    while bucket and bucket[0] <= now - RATE_LIMIT_WINDOW:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX:
        return True
    bucket.append(now)
    return False


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.client.host if request.client else "unknown")[:64]


# --- Admin gate (fail-closed: unset token denies everything) ---
def _require_admin(request: Request) -> str:
    expected = os.getenv("LICENSE_ADMIN_TOKEN", "")
    provided = request.headers.get("x-license-admin-token", "")
    if not expected or not provided or not hmac.compare_digest(provided, expected):
        logger.warning("admin endpoint denied")
        raise HTTPException(status_code=401, detail="admin authentication required")
    return "license-admin"

# --- Key management ---
# Overridable for tests/staging. Production values come from the systemd
# EnvironmentFile, never from this repository.
KEYS_DIR = Path(os.getenv("LICENSE_KEYS_DIR", "/home/cvsz/.config/zeaz"))
PRIVATE_KEY_FILE = KEYS_DIR / "license_server_private_key.pem"
PUBLIC_KEY_FILE = KEYS_DIR / "license_server_public_key.pem"
SIGNING_KID = os.getenv("LICENSE_SIGNING_KID", "e58bc8616e5d12cf")

CANONICAL_FEATURES = ["catalog", "favorites", "submit_film", "creator_submission",
                      "cinema.creator", "license_verification"]


def _seed_keys() -> list[str]:
    """License keys pre-registered from the secret environment (comma-separated)."""
    return [k.strip() for k in os.getenv("LICENSE_SEED_KEYS", "").split(",") if k.strip()]

def load_or_generate_keys():
    """Load existing keys or generate new Ed25519 key pair."""
    if PRIVATE_KEY_FILE.exists() and PUBLIC_KEY_FILE.exists():
        with open(PRIVATE_KEY_FILE, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(PUBLIC_KEY_FILE, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
        logger.info("Loaded existing Ed25519 keys")
    else:
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        KEYS_DIR.mkdir(parents=True, exist_ok=True)
        with open(PRIVATE_KEY_FILE, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open(PUBLIC_KEY_FILE, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        logger.info("Generated new Ed25519 key pair")
    return private_key, public_key

private_key, public_key = load_or_generate_keys()

def base64url_encode(data: dict) -> str:
    """Encode a dict to base64url without padding."""
    json_bytes = json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode()
    return base64.urlsafe_b64encode(json_bytes).decode().rstrip("=")

def sign_jwt(header: dict, claims: dict) -> str:
    """Create a signed JWT using Ed25519."""
    header_b64 = base64url_encode(header)
    claims_b64 = base64url_encode(claims)
    signing_input = f"{header_b64}.{claims_b64}".encode()
    
    signature = private_key.sign(signing_input)
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    return f"{header_b64}.{claims_b64}.{sig_b64}"

def get_public_key_base64url() -> str:
    """Get public key as base64url encoded string (as used by license.php)."""
    # The public key for Ed25519 is 32 bytes
    raw_key = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return base64.urlsafe_b64encode(raw_key).decode().rstrip("=")

# --- License store ---
class LicenseStore:
    def __init__(self):
        self.licenses = {}
        self.activations = {}
        self.revoked = set()
        self.products = {
            "zmovie": {
                "name": "ZeaZ Cinema",
                # 'cinema.creator' is the canonical entitlement name per the
                # token contract; legacy aliases retained for compatibility.
                "features": list(CANONICAL_FEATURES),
                "active": True
            }
        }

    def get_license(self, key: str):
        if key not in self.licenses:
            # Pre-registered keys come from LICENSE_SEED_KEYS only.
            if key in _seed_keys():
                self.licenses[key] = {
                    "product": "zmovie",
                    "features": list(CANONICAL_FEATURES),
                    "active": True,
                    "created": time.time(),
                    "expires": None
                }
                logger.info(f"Registered license key: {key[:8]}...")
            else:
                return None
        return self.licenses[key]
    
    def is_active(self, key: str) -> bool:
        license_data = self.get_license(key)
        if not license_data:
            return False
        if key in self.revoked:
            return False
        if license_data.get("expires") and license_data["expires"] < time.time():
            return False
        return True

store = LicenseStore()

# --- Models ---
class ActivateRequest(BaseModel):
    key: str
    product: str = Field(..., pattern="^zmovie$")
    site_url: str = Field(..., pattern="^https://zmovie\\.zeaz\\.dev$")

class ActivateResponse(BaseModel):
    lease: str
    activation_id: str


class RevokeRequest(BaseModel):
    key: str = Field(min_length=8, max_length=256)


class ExpireRequest(BaseModel):
    key: str = Field(min_length=8, max_length=256)
    expires_in_seconds: int = Field(ge=-86400 * 365, le=86400 * 365 * 5)


class FeaturesRequest(BaseModel):
    key: str = Field(min_length=8, max_length=256)
    features: list[str] = Field(max_length=32)

# --- Routes ---
@app.get("/health")
def health():
    return {"status": "healthy", "service": "zeaz-license-server", "version": "1.0.0"}

@app.post("/v1/activate", response_model=ActivateResponse)
async def activate(req: ActivateRequest, request: Request):
    """Activate a license key and return a signed lease token."""
    client = _client_ip(request)
    if _rate_limited(client):
        logger.warning(f"activation rate-limited: client={client}")
        raise HTTPException(status_code=429, detail="rate limit exceeded",
                            headers={"Retry-After": str(RATE_LIMIT_WINDOW)})
    key = req.key.strip()

    if not store.is_active(key):
        logger.info(f"activation denied: key={key[:8]}... site={req.site_url}")
        raise HTTPException(status_code=404, detail="Invalid or revoked license key")
    
    license_data = store.get_license(key)
    
    # Generate activation ID
    activation_id = secrets.token_hex(16)
    
    # Build JWT claims matching license.php expectations
    now = int(time.time())
    claims = {
        "iss": "zeaz-license",
        "aud": "zmovie",
        "site": req.site_url,
        "sub": key,
        "activation_id": activation_id,
        "iat": now,
        "nbf": now,
        "exp": now + 900,  # 15 minutes
        "features": license_data["features"]
    }
    
    # Sign the token
    header = {"alg": "EdDSA", "kid": SIGNING_KID, "typ": "JWT"}
    token = sign_jwt(header, claims)
    
    store.activations[activation_id] = {
        "key": key,
        "site_url": req.site_url,
        "timestamp": now,
        "product": license_data["product"]
    }
    
    logger.info(f"License activated: key={key[:8]}... site={req.site_url} activation={activation_id}")
    
    return ActivateResponse(lease=token, activation_id=activation_id)

@app.get("/v1/public-key")
def public_key_endpoint():
    """Return the public verification key (base64url Ed25519)."""
    pub_key_b64 = get_public_key_base64url()
    return {"public_key": pub_key_b64}

@app.get("/v1/leases/{activation_id}")
def get_lease(activation_id: str, request: Request):
    """Get lease details by activation ID (admin only)."""
    _require_admin(request)
    lease = store.activations.get(activation_id)
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")
    return lease


@app.post("/v1/admin/revoke")
def admin_revoke(req: RevokeRequest, request: Request):
    """Revoke a license key (admin only). Effective until process restart;
    persistent revocation list lands with the systemd/DB phase."""
    _require_admin(request)
    key = req.key.strip()
    store.revoked.add(key)
    logger.info(f"license revoked: key={key[:8]}...")
    return {"revoked": True}


@app.post("/v1/admin/expire")
def admin_expire(req: ExpireRequest, request: Request):
    """Set a license expiry timestamp (admin only, for testing lifecycle)."""
    _require_admin(request)
    key = req.key.strip()
    data = store.get_license(key)
    if data is None:
        raise HTTPException(status_code=404, detail="license key not found")
    data["expires"] = time.time() + req.expires_in_seconds
    logger.info(f"license expiry set: key={key[:8]}... expires_in={req.expires_in_seconds}s")
    return {"expired": req.expires_in_seconds <= 0}


@app.post("/v1/admin/features")
def admin_features(req: FeaturesRequest, request: Request):
    """Replace the feature list for a key (admin only, for entitlement testing)."""
    _require_admin(request)
    key = req.key.strip()
    data = store.get_license(key)
    if data is None:
        raise HTTPException(status_code=404, detail="license key not found")
    clean = [str(f).strip()[:80] for f in req.features if str(f).strip()][:32]
    data["features"] = clean
    logger.info(f"license features set: key={key[:8]}... count={len(clean)}")
    return {"features": clean}

if __name__ == "__main__":
    import uvicorn
    logger.info("License Server starting on 127.0.0.1:8085")
    pub_b64 = get_public_key_base64url()
    logger.info(f"Public key (base64url, {len(pub_b64)} chars): {pub_b64}")
    uvicorn.run(app, host="127.0.0.1", port=8085)
