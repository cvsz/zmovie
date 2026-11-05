# Docker deployment

See the [documentation index](../docs/INDEX.md) for canonical guides and
cross-component procedures.

Docker deployment runs the API as an unprivileged user, mounts persistent data,
exposes the configured HTTP port, and performs health checks against
`/api/v2/health`. API documentation is disabled by default; set
`ZMOVIE_ENABLE_DOCS=true` in the Compose environment only for controlled
debugging.

ตั้ง `ZMOVIE_SECRET_KEY` ก่อนเปิด port ออก network; service จะปฏิเสธการเริ่ม
หาก bind แบบ network โดยปิด auth หรือไม่มี key ถาวรอย่างน้อย 32 ตัวอักษร
เมื่อเปิด OAuth จาก public domain ให้ตั้ง `ZMOVIE_BASE_URL` เป็น HTTPS origin
ของเว็บไซต์ ค่าเริ่มต้นว่างใช้ได้เฉพาะการเข้าผ่าน loopback
