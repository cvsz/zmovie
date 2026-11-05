# Authentication bootstrap

See the [documentation index](../docs/INDEX.md) for canonical guides and
cross-component procedures.

การสร้างผู้ดูแลผ่าน HTTP ใช้ได้เมื่อ service bind ที่ loopback และ client เชื่อมต่อ
จาก loopback เท่านั้น ระบบสร้างบัญชีภายใต้ SQLite `BEGIN IMMEDIATE` จึงมีผู้ชนะ
ได้เพียงคำขอเดียวเมื่อมีคำขอพร้อมกัน หลังเริ่มระบบแล้วให้ใช้บัญชีจาก
`ZMOVIE_ADMIN_USER` และ `ZMOVIE_ADMIN_PASSWORD` ที่เก็บใน environment file
สิทธิ์จำกัดแทนการเปิด bootstrap ผ่าน network

การ bind ออกนอก loopback ต้องเปิด `ZMOVIE_AUTH_ENABLED=true` และตั้ง
`ZMOVIE_SECRET_KEY` แบบถาวรอย่างน้อย 32 ตัวอักษร ระบบตรวจค่าก่อนเริ่มรับงาน
และปฏิเสธการตั้งค่าที่ไม่ผ่าน ส่วน OAuth บน public host ต้องกำหนด
`ZMOVIE_BASE_URL` เป็น HTTPS origin ที่ถูกต้อง
