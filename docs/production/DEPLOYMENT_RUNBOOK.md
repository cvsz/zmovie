# Deployment Runbook — zMovie + ZeaZ Cinema

> คู่มือ deploy ปฏิบัติการ (ภาษาไทย) — versioned, ทดสอบซ้ำได้, rollback ได้

## 1. สภาพแวดล้อม

| Env | ใช้ทำอะไร | ข้อมูล |
|---|---|---|
| Production | ให้บริการจริง `https://zmovie.zeaz.dev/` + `/cinema/` | DB `zmovie_cinema`, ไฟล์ `/var/www/zmovie-cinema` |
| Staging | ทดสอบก่อน production (แยก DB/ไฟล์/host) | ห้ามใช้ข้อมูล production ตรง ๆ |

**กฎเหล็ก:** staging/production แยกกันทุกชั้น, ห้าม expose
origins (`127.0.0.1:8080`, `127.0.0.1:3306`) หรือ DB สู่ internet,
TLS/Cloudflare Tunnel ดูแล ingress, firewall (UFW) เปิดเฉพาะ 22/80/443

## 2. Versioned deployments

- Deploy ตาม commit ที่ review แล้ว (ห้าม `git clone --branch main` ลอย ๆ
  สำหรับ production ถ้าไม่ pin — บันทึก commit SHA ใน release notes)
- Native: `install.sh upgrade` (backup SQLite อัตโนมัติก่อนแทนโค้ด,
  ปฏิเสธ upgrade ถ้ามี worker lease/active หรือ publication ค้าง)
- Docker: `docker compose up -d --build` + `docker compose config --quiet`
- WordPress: `wp-installer/install.sh` (idempotent) + flush rewrite +
  ตรวจ plugin/theme status

## 3. Pre-deployment checklist

1. `git status` สะอาด, รู้ commit ที่จะ deploy
2. สำรองข้อมูล: `sudo /opt/backups/wordpress-backup.sh` (WP) +
   `python -m zmovie_platform.runtime_ops backup` (SQLite)
3. `terraform fmt -check`, `validate`, `plan` (infra ใน zworkforce,
   ห้าม apply ที่ทำลาย DNS/routes โดยไม่ review)
4. รัน smoke: `bash scripts/smoke-deploy.sh`
5. แจ้ง maintenance window ถ้ากระทบผู้ใช้

## 4. Probes

| Probe | Endpoint | ใช้เมื่อ |
|---|---|---|
| Liveness | `GET /api/v2/livez` → `{"status":"alive"}` | process ยังอยู่ไหม (ไม่แตะ DB) |
| Readiness | `GET /api/v2/readyz` → `{"status":"ready"}` | DB/migrations พร้อมรับงานไหม |
| Health | `GET /api/v2/health` | รายงานละเอียด (redacted) |
| Capabilities | `GET /api/v2/capabilities` | version/providers/features |

Docker `HEALTHCHECK` + compose `healthcheck` ใช้ health endpoint อยู่แล้ว

## 5. Smoke tests หลัง deploy

```bash
ZMOVIE_URL=http://127.0.0.1:8080 bash scripts/smoke-deploy.sh
curl -s -o /dev/null -w '%{http_code}\n' https://zmovie.zeaz.dev/cinema/
curl -s -o /dev/null -w '%{http_code}\n' https://zmovie.zeaz.dev/cinema/wp-json/
bash scripts/check-backup.sh
ZEAZ_LICENSE_API=http://127.0.0.1:8085 bash scripts/check-license-api.sh
```

## 6. Monitoring & alerting

Wired crons (cvsz; logs to `~/.local/share/zmovie-checks.log`, no MTA on host):

- `15 2 * * * .../check-backup.sh` — WP backup freshness + integrity
- `30 6 * * * .../check-disk.sh` — disk warn 85% / crit 95%
- `5 * * * * .../check-license-api.sh` — License API availability
- root `0 3 * * 0 .../backup-dr.sh` — weekly protected DR snapshot

| สัญญาณ | วิธีตรวจ | alert |
|---|---|---|
| Backup ล้มเหลว/เก่า | `check-backup.sh` daily cron | exit ≠ 0 → check log |
| License API ดับ | `check-license-api.sh` hourly cron | exit ≠ 0 → check log |
| Media queue ค้าง | `zmovie-ctl worker-status`, watchdog status | journal + status |
| Disk เต็ม | `check-disk.sh` daily cron (warn 85 / crit 95) | exit ≠ 0 → check log |
| Service ดับ | `systemctl is-active`, `journalctl -u zmovie*` | watchdog repair + log |

ยังไม่มี PagerDuty/MTA — ขั้นต่ำคือ cron + log file + บันทึก incident.
Known live alert (2026-09-24): disk 99% ทำ `zmovie-backup.service`
fail ด้วย sqlite I/O error — mechanism ปกติ (พิสูจน์ด้วย manual run
สำเร็จ) ต้องเคลียร์พื้นที่ ห้ามลบข้อมูล operator โดยพลการ.

## 7. Rollback

- **zMovie code:** ใช้ SQLite backup ก่อน upgrade (`runtime_ops backup`) +
  `upgrade-readiness` gate; ถ้า deploy พังให้คืนโค้ด commit เดิมแล้ว restore DB
  ตาม `docs/BACKUP_AND_RECOVERY.md`
- **WordPress:** ตาม `docs/runbooks/WORDPRESS_BACKUP_RESTORE.md`
  (isolated restore ก่อนเสมอ) + rollback plugin/theme จาก tar backup
- **Infra:** `terraform plan` ต้อง zero-destruction; ถ้าผิดให้ revert config
  แล้ว `plan` ใหม่ ห้าม `apply` ทับโดยไม่ review

## 8. Logs / Metrics

- Structured logs: `zmovie_platform/logging_config.py` + `journalctl -u zmovie*`
- Audit: `data/audit.jsonl` (publication/commerce/ticketing/privacy)
- Metrics: `GET /api/v2/metrics` (auth required)
- Nginx: `/var/log/nginx/*`, PHP-FPM: `php-fpm.log`, MariaDB: error log

## 9. Incident response

1. ตรวจ probes + logs (redact secret ก่อนแชร์)
2. แยกผลกระทบ (Studio / Cinema / License / Commerce / Ticketing)
3. Mitigate (rollback/revert/scale) ก่อนหาสาเหตุ
4. ถ้ามี secret หลุด: rotate ทันทีตาม `docs/security/LICENSE_KEY_MANAGEMENT.md` §4
5. เขียน post-mortem: root cause, fix, validation, วิธีป้องกัน

## 10. Dependency policy

- Dependabot + `pip-audit` ใน CI, `ruff`, `shellcheck`, PHP lint
- อัปเดตทีละ dependency พร้อมรัน full test + smoke-deploy
- Container: `docker build` ใน CI ทุก PR; image scan ก่อน production tag
