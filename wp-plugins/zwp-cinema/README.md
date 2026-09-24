# ZeaZ Cinema — WordPress Plugin ของ ZeaZDev (Alpha)

ปลั๊กอินที่พัฒนาขึ้นใหม่สำหรับ **Film Catalog, Trailer Feed, Genres, Favorites และ Creator Submission** โดยไม่คัดลอก ไม่เปลี่ยนระบบ Activate และไม่แตะ Site Key ของ WP-Script หากติดตั้งผลิตภัณฑ์ของ WP-Script แยกต่างหาก ยังคงต้องใช้ License ที่ถูกต้องจากผู้ผลิต

## ติดตั้งบน Staging

1. ใช้ WordPress 6.4+ และ PHP 8.1+ พร้อม Sodium บนระบบ Staging ที่แยกจาก Production
2. คัดลอก `wp-plugins/zwp-cinema/` ไปยัง `wp-content/plugins/zwp-cinema/` แล้ว Activate **ZeaZ Cinema**
3. ไปที่ Settings → Permalinks แล้วกด Save หนึ่งครั้ง
4. ในเมนู Cinema Films ให้ Administrator เพิ่มภาพยนตร์ ระบุ HTTPS URL ของไฟล์ MP4/WebM ที่มีสิทธิ์เผยแพร่ เพิ่ม Featured Image และเลือก Genre ก่อน Publish
5. ติดตั้ง Theme `themes/zwp-cinema/` เพื่อเปิดใช้ Homepage และ Swipe Feed

ไม่มีภาพยนตร์ Poster หรือตัวอย่างหนังของบุคคลที่สามรวมอยู่ใน Source Code ต้องใช้ Media ที่มีสิทธิ์เผยแพร่จริงเท่านั้น

## ZeaZ License — สำหรับฟีเจอร์ Creator

Public Feed, Film Details และการจัดการโดย Administrator ไม่จำเป็นต้องมี License ส่วนการส่งภาพยนตร์จาก Creator ผ่าน Shortcode `[zwpc_submit]` ใช้ Feature `cinema.creator` ที่ตรวจสอบจาก ZeaZ License Server ซึ่งเป็นระบบของเราเอง

ให้สร้าง License ของ Product `zmovie` บน Server แล้วเก็บ Key ใน Secret Manager กำหนดค่าผ่าน `wp-config.php` หรือการ Inject Secret จาก Host:

```php
define('ZEAZ_LICENSE_API', 'https://license.example.com');
define('ZEAZ_LICENSE_ORIGIN', 'https://cinema.example.com');
define('ZEAZ_LICENSE_KEY', getenv('ZEAZ_LICENSE_KEY'));
define('ZEAZ_LICENSE_PUBLIC_KEY', getenv('ZEAZ_LICENSE_PUBLIC_KEY'));
```

`ZEAZ_LICENSE_PUBLIC_KEY` ต้องเป็น Ed25519 Public Key ที่ Pin จากช่องทางที่เชื่อถือได้ **ห้าม** นำ Private Signing Key เข้า WordPress และห้ามนำ License จริงเข้า Git หรือ Log ระบบจะตรวจ Digital Signature, Audience, Issuer, Site Origin และเวลาหมดอายุของ Signed Lease หากตรวจสอบไม่ได้จะปิด Creator Submission โดยอัตโนมัติ Cached Lease มีอายุไม่เกิน 60 วินาที จึงมีความล่าช้าของการระงับสิทธิ์ได้ในช่วงเวลานี้ ห้ามใช้ Lease ดังกล่าวแทนการตรวจสอบสิทธิ์ของ Payment, Ticketing หรือ DRM

ปัจจุบัน Plugin ต้องเชื่อมต่อ License API ผ่าน HTTPS; ไม่รองรับ HTTP Local Development โดยปริยาย

## REST API

| Endpoint | สิทธิ์ | การทำงาน |
| --- | --- | --- |
| `GET /wp-json/zwpc/v1/feed?page=1&genre=drama` | Public | แสดงภาพยนตร์ที่ Publish แล้ว ครั้งละ 6 รายการ |
| `GET /wp-json/zwpc/v1/favorites` | Login | ส่งคืน ID ภาพยนตร์ที่บันทึกไว้ |
| `POST /wp-json/zwpc/v1/favorites/{id}` | Login + WP REST Nonce | เพิ่มหรือลบรายการโปรด |

สร้างหน้า WordPress ชื่อ `Favorites` แล้วใส่ Shortcode `[zwpc_favorites]` เพื่อแสดงรายการโปรด สร้างหน้า `Submit Film` พร้อม `[zwpc_submit]` เพื่อให้ Creator ส่ง URL, Synopsis และยืนยันสิทธิ์เผยแพร่ ทุก Submission จะมีสถานะ `pending` จนกว่า Administrator จะอนุมัติ ไม่เปิดให้ Creator Publish ผ่าน WordPress REST API โดยตรง

## ข้อจำกัดและ Security Gates

- ยังไม่มี File Upload, Transcoding, Malware Scan, Payment, Seat Reservation, DRM, Premium Paywall หรือ Automatic Publication
- รับเพียง HTTPS URL ที่ชี้ไปยัง MP4/WebM โดยไม่ Download ไฟล์จาก URL นั้น ผู้ดูแลต้องตรวจ Rights และ Media Host ก่อน Publish
- Favorites ใช้ WordPress User Meta; การเขียนพร้อมกันหลายรายการยังเป็น Last-Write-Wins
- Creator Submission ใช้ Login, CSRF Nonce, License Verification, URL Validation และ Rights Assertion แต่ต้องทดสอบ WordPress Runtime จริงก่อนใช้งานสาธารณะ

**Acceptance บน Staging:** ทดสอบ Anonymous/Subscriber/Admin, REST Nonce, Film Publish, Favorite Toggle, Creator Pending Review, License ที่ถูกต้อง/หมดอายุ/ถูก Revoke/Wrong Site และการไม่ปรากฏ Secret ใน HTML/REST ก่อนเปิดใช้งานจริง
