from __future__ import annotations

import json
import secrets
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client

from .storage import connect
from .auth import create_user, issue_token


@dataclass(frozen=True)
class OAuthProvider:
    name: str
    display_name: str
    client_id: str
    client_secret: str
    issuer_url: str
    authorize_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    scopes: tuple[str, ...] = ("openid", "email", "profile")
    pkce: bool = True
    extra_authorize_params: dict[str, str] | None = None


class OAuthManager:
    def __init__(self, providers: dict[str, OAuthProvider]):
        self._providers = providers
        self._state_store: dict[str, tuple[str, str, float]] = {}  # state -> (provider_name, code_verifier, expires_at)

    def get_provider(self, name: str) -> OAuthProvider | None:
        return self._providers.get(name)

    def list_providers(self) -> list[dict[str, str]]:
        return [
            {"name": p.name, "display_name": p.display_name}
            for p in self._providers.values()
        ]

    def create_authorization_url(self, provider_name: str, redirect_uri: str) -> tuple[str, str]:
        provider = self._providers[provider_name]
        if provider is None:
            raise ValueError(f"Unknown OAuth provider: {provider_name}")

        state = secrets.token_urlsafe(32)
        code_verifier = secrets.token_urlsafe(64) if provider.pkce else ""
        code_challenge = ""
        if provider.pkce:
            import hashlib
            import base64
            challenge = hashlib.sha256(code_verifier.encode()).digest()
            code_challenge = base64.urlsafe_b64encode(challenge).rstrip(b"=").decode()

        self._state_store[state] = (provider_name, code_verifier, time.time() + 600)  # 10 min expiry

        client = AsyncOAuth2Client(
            client_id=provider.client_id,
            client_secret=provider.client_secret,
            redirect_uri=redirect_uri,
            scope=" ".join(provider.scopes),
        )

        params = {
            "response_type": "code",
            "state": state,
        }
        if provider.pkce:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        if provider.extra_authorize_params:
            params.update(provider.extra_authorize_params)

        auth_url = client.create_authorization_url(provider.authorize_endpoint, **params)
        return auth_url, state

    async def exchange_code(
        self,
        provider_name: str,
        redirect_uri: str,
        code: str,
        state: str,
    ) -> dict[str, Any]:
        provider = self._providers[provider_name]
        if provider is None:
            raise ValueError(f"Unknown OAuth provider: {provider_name}")

        stored = self._state_store.pop(state, None)
        if not stored:
            raise ValueError("Invalid or expired OAuth state")
        stored_provider, code_verifier, expires_at = stored
        if stored_provider != provider_name:
            raise ValueError("OAuth state provider mismatch")
        if expires_at < time.time():
            raise ValueError("OAuth state expired")

        client = AsyncOAuth2Client(
            client_id=provider.client_id,
            client_secret=provider.client_secret,
            redirect_uri=redirect_uri,
            scope=" ".join(provider.scopes),
        )

        token_params = {}
        if provider.pkce and code_verifier:
            token_params["code_verifier"] = code_verifier

        token = await client.fetch_token(
            provider.token_endpoint,
            code=code,
            **token_params,
        )

        # Fetch user info
        userinfo = await self._fetch_userinfo(client, provider)
        return {
            "provider": provider_name,
            "token": token,
            "userinfo": userinfo,
        }

    def create_authorization_url_for_provider(self, provider_name: str, redirect_uri: str) -> tuple[str, str]:
        """Alias for create_authorization_url - kept for clarity."""
        return self.create_authorization_url(provider_name, redirect_uri)

    async def exchange_code_for_provider(
        self,
        provider_name: str,
        redirect_uri: str,
        code: str,
        state: str,
    ) -> dict[str, Any]:
        """Alias for exchange_code - kept for clarity."""
        return await self.exchange_code(provider_name, redirect_uri, code, state)

    async def _fetch_userinfo(self, client: AsyncOAuth2Client, provider: OAuthProvider) -> dict[str, Any]:
        resp = await client.get(provider.userinfo_endpoint)
        resp.raise_for_status()
        return resp.json()

    def cleanup_expired_states(self) -> None:
        now = time.time()
        expired = [k for k, v in self._state_store.items() if v[2] < now]
        for k in expired:
            self._state_store.pop(k, None)


def build_oauth_manager_from_env() -> OAuthManager:
    """Build OAuthManager from environment variables.

    Expected env vars (per provider):
    - OAUTH_{NAME}_CLIENT_ID
    - OAUTH_{NAME}_CLIENT_SECRET
    - OAUTH_{NAME}_ISSUER_URL
    - OAUTH_{NAME}_DISPLAY_NAME (optional)
    - OAUTH_{NAME}_SCOPES (optional, comma-separated)
    - OAUTH_{NAME}_PKCE (optional, "true"/"false")

    Example for WordPress (with WP OAuth Server plugin):
    OAUTH_WORDPRESS_CLIENT_ID=xxx
    OAUTH_WORDPRESS_CLIENT_SECRET=yyy
    OAUTH_WORDPRESS_ISSUER_URL=https://wp.example.com
    OAUTH_WORDPRESS_DISPLAY_NAME=WordPress
    OAUTH_WORDPRESS_SCOPES=openid,email,profile
    OAUTH_WORDPRESS_PKCE=true
    """
    import os
    import re

    providers = {}
    prefix = "OAUTH_"
    seen = set()

    for key in os.environ:
        if not key.startswith(prefix):
            continue
        # Extract provider name (everything between OAUTH_ and _CLIENT_ID/SECRET/etc)
        match = re.match(r"^OAUTH_([A-Z0-9_]+)_(CLIENT_ID|CLIENT_SECRET|ISSUER_URL|DISPLAY_NAME|SCOPES|PKCE)$", key)
        if not match:
            continue
        provider_name = match.group(1).lower()
        seen.add(provider_name)

    for name in seen:
        client_id = os.getenv(f"OAUTH_{name.upper()}_CLIENT_ID", "").strip()
        client_secret = os.getenv(f"OAUTH_{name.upper()}_CLIENT_SECRET", "").strip()
        issuer_url = os.getenv(f"OAUTH_{name.upper()}_ISSUER_URL", "").strip()
        if not (client_id and client_secret and issuer_url):
            continue

        display_name = os.getenv(f"OAUTH_{name.upper()}_DISPLAY_NAME", name.title())
        scopes_str = os.getenv(f"OAUTH_{name.upper()}_SCOPES", "openid,email,profile").strip()
        scopes = tuple(s.strip() for s in scopes_str.split(",") if s.strip())
        pkce = os.getenv(f"OAUTH_{name.upper()}_PKCE", "true").lower() in ("1", "true", "yes")

        # Build endpoints from issuer URL (OIDC discovery)
        authorize_endpoint = f"{issuer_url.rstrip('/')}/oauth/authorize"
        token_endpoint = f"{issuer_url.rstrip('/')}/oauth/token"
        userinfo_endpoint = f"{issuer_url.rstrip('/')}/oauth/userinfo"

        # Try OIDC discovery for standard endpoints
        try:
            import httpx as _httpx
            disco_resp = _httpx.get(f"{issuer_url.rstrip('/')}/.well-known/openid-configuration", timeout=5.0)
            if disco_resp.is_success:
                disco = disco_resp.json()
                authorize_endpoint = disco.get("authorization_endpoint", authorize_endpoint)
                token_endpoint = disco.get("token_endpoint", token_endpoint)
                userinfo_endpoint = disco.get("userinfo_endpoint", userinfo_endpoint)
        except Exception:
            pass  # Use defaults

        providers[name] = OAuthProvider(
            name=name,
            display_name=display_name,
            client_id=client_id,
            client_secret=client_secret,
            issuer_url=issuer_url,
            authorize_endpoint=authorize_endpoint,
            token_endpoint=token_endpoint,
            userinfo_endpoint=userinfo_endpoint,
            scopes=scopes,
            pkce=pkce,
        )

    return OAuthManager(providers)


async def find_or_create_oauth_user(
    provider_name: str,
    userinfo: dict[str, Any],
) -> dict[str, Any]:
    """Find existing user linked to OAuth provider, or create new one.

    Links by email if available, otherwise by provider+subject.
    """
    email = userinfo.get("email")
    sub = str(userinfo.get("sub") or userinfo.get("id") or "")
    if not sub:
        raise ValueError("OAuth userinfo missing subject/ID")

    with connect() as conn:
        # Try to find by email first
        if email:
            row = conn.execute(
                "SELECT id,username,role FROM users WHERE email=?",
                (email.lower(),),
            ).fetchone()
            if row:
                # Link OAuth if not already linked
                conn.execute(
                    """INSERT OR IGNORE INTO oauth_links(user_id, provider, provider_sub)
                       VALUES(?,?,?)""",
                    (row["id"], provider_name, sub),
                )
                conn.commit()
                return {"id": row["id"], "username": row["username"], "role": row["role"]}

        # Try to find by provider+sub
        row = conn.execute(
            """SELECT u.id,u.username,u.role FROM users u
               JOIN oauth_links o ON u.id=o.user_id
               WHERE o.provider=? AND o.provider_sub=?""",
            (provider_name, sub),
        ).fetchone()
        if row:
            return {"id": row["id"], "username": row["username"], "role": row["role"]}

        # Create new user
        # Generate username from email or provider+sub
        if email:
            base_username = email.split("@")[0].lower()
        else:
            base_username = f"{provider_name}_{sub[:8]}"

        # Ensure unique username
        username = base_username
        counter = 1
        while True:
            try:
                with connect() as conn2:
                    cur = conn2.execute(
                        "INSERT INTO users(username,password_hash,role,email) VALUES(?,?,?,?)",
                        (username, "", "user", email or ""),
                    )
                    user_id = cur.lastrowid
                    conn2.execute(
                        "INSERT INTO oauth_links(user_id, provider, provider_sub) VALUES(?,?,?)",
                        (user_id, provider_name, sub),
                    )
                    conn2.commit()
                break
            except Exception:
                counter += 1
                username = f"{base_username}{counter}"

        return {"id": user_id, "username": username, "role": "user"}


def ensure_oauth_tables() -> None:
    """Create OAuth linking tables if they don't exist."""
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS oauth_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                provider_sub TEXT NOT NULL,
                created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
                UNIQUE(user_id, provider),
                UNIQUE(provider, provider_sub)
            )
        """)
        # Add email column to users if not exists
        try:
            conn.execute("ALTER TABLE users ADD COLUMN email TEXT DEFAULT ''")
        except Exception:
            pass  # Column exists
        conn.commit()