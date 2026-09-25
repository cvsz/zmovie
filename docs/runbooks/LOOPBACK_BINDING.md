# Runbook — zMovie Loopback Binding (defense in depth)

Status: PREPARED, NOT APPLIED. Applying requires an operator-approved
maintenance window because it restarts the production web service.

## 1. Current state (verified 2026-09-25, host `core.zeaz.dev`)

```text
zmovie.service ExecStart --host 0.0.0.0 --port $ZMOVIE_PORT
listener: 0.0.0.0:8080 (uvicorn pid owned by zmovie.service)
Nginx: proxy_pass http://127.0.0.1:8080   (only local consumer)
Cloudflare Tunnel origin: http://127.0.0.1:80 (Nginx), never :8080
Containers publishing host :8080: none
UFW: 8080 DENY, 8000 DENY (keep as defense in depth)
```

Exposure is currently mitigated by UFW, not by the bind address.

## 2. Prepared artifacts

- `deploy/systemd/zmovie-loopback-bind.conf.example` — drop-in for hosts on
  the previous installer (replaces `ExecStart`, loopback only).
- `install.sh` now renders `--host "${ZMOVIE_HOST:-0.0.0.0}"`. Existing env
  files keep `ZMOVIE_HOST=0.0.0.0`, so nothing changes until an operator
  sets `ZMOVIE_HOST=127.0.0.1`. Fully backward compatible.

## 3. Apply (approved window only)

```bash
# 1) pre-change backup
sudo cp -a /etc/systemd/system/zmovie.service /etc/systemd/system/zmovie.service.bak-$(date -u +%Y%m%dT%H%M%SZ)
sudo cp -a /etc/zmovie/zmovie.env /etc/zmovie/zmovie.env.bak-$(date -u +%Y%m%dT%H%M%SZ)

# 2) new-install path (preferred, no drop-in)
sudo sed -i 's/^ZMOVIE_HOST=.*/ZMOVIE_HOST=127.0.0.1/' /etc/zmovie/zmovie.env
sudo install -m 0644 /etc/systemd/system/zmovie.service /etc/systemd/system/zmovie.service.new
sudo sed -i "s|--host 0.0.0.0|--host \"\\\${ZMOVIE_HOST:-0.0.0.0}\"|" /etc/systemd/system/zmovie.service.new
sudo mv /etc/systemd/system/zmovie.service.new /etc/systemd/system/zmovie.service
# legacy path instead: install the drop-in from deploy/systemd/

# 3) apply
sudo systemctl daemon-reload
sudo systemctl restart zmovie
```

## 4. Verify (all must pass)

```bash
ss -tlnp | grep 8080                 # expect 127.0.0.1:8080 only
curl -fsS http://127.0.0.1:8080/api/v2/health | head -c 120
sudo nginx -t
curl -sk -o /dev/null -w '%{http_code}\n' https://zmovie.zeaz.dev/          # 307
curl -sk -o /dev/null -w '%{http_code}\n' https://zmovie.zeaz.dev/cinema/   # 200
curl -sk -o /dev/null -w '%{http_code}\n' https://zmovie.zeaz.dev/cinema/wp-json/  # 200
curl -sk -o /dev/null -w '%{http_code}\n' https://license.zeaz.dev/health    # 200
sudo zmovie-ctl worker-status           # worker still draining the queue
```

`0.0.0.0:8080` must no longer appear in `ss` output. Keep the UFW DENY rule.

## 5. Rollback

```bash
sudo cp -a /etc/systemd/system/zmovie.service.bak-<ts> /etc/systemd/system/zmovie.service
sudo cp -a /etc/zmovie/zmovie.env.bak-<ts> /etc/zmovie/zmovie.env
sudo rm -f /etc/systemd/system/zmovie.service.d/10-loopback-bind.conf
sudo systemctl daemon-reload && sudo systemctl restart zmovie
curl -fsS http://127.0.0.1:8080/api/v2/health >/dev/null && echo rolled-back-ok
```

## 6. Not applicable

Docker Compose deployments publish the port themselves
(`${ZMOVIE_PORT:-8080}:8080`); this runbook covers native systemd only.
