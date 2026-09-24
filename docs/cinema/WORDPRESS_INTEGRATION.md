# ZeaZ Cinema — แผนและสถานะ WordPress Integration

## ขอบเขตงาน

พัฒนา WordPress Plugin และ Theme ของ ZeaZDev เองสำหรับภาพยนตร์และ Trailer ตามแนวคิด Vertical Swipe, Favorites, Creator Registration, Front-end Submission และ AJAX Pagination ที่ปรากฏใน [TikSwipe Features](https://www.wp-script.com/adult-wordpress-themes/tikswipe/) ซึ่งตรวจสอบเมื่อ 24 กันยายน 2026 ระบบวิจัยไม่สามารถเปิด Live Demo Endpoint ได้ จึงไม่อ้างว่า Layout เหมือน Demo ทุกพิกเซล และไม่ใช้ Source/Asset ของ Theme เชิงพาณิชย์ต้นทาง

ไฟล์ที่เพิ่ม: `wp-plugins/zwp-cinema/` สำหรับ Film Catalog, Genre, REST API, Favorites, Moderated Creator Submission และ ZeaZ License Verification; `themes/zwp-cinema/` สำหรับ Responsive Cinema UI, Video Feed, Film Detail, Creator Profile และ Shortcode Page

ระบบ Python ของ `cvsz/zmovie` ได้แก่ Studio, Render Worker, Media QC และ Publishing Approval ไม่ถูกแก้ไขในรอบนี้ การนำ Media ที่ Render จาก zMovie มา Publish บน WordPress ต้องพัฒนา Explicit Opt-in Integration พร้อม Media Rights และ Human Approval เพิ่มเติมใน Phase ถัดไป

## ขอบเขต License

Plugin ใช้ ZeaZ License Server ของเราเอง Product `zmovie` และ Feature `cinema.creator` โดยตรวจ Signature ด้วย Public Key แบบ Pin และกำหนดอายุ Cached Lease ไม่เกิน 60 วินาที ไม่มีการแตะ `wpscore_site_key` หรือปลอมแปลง Entitlement ของ WP-Script หากต้องการติดตั้งผลิตภัณฑ์ต้นทางแยกต่างหากยังต้องใช้ License ของผู้ผลิต

## หลักฐานและสิ่งที่ยังขาด

เพิ่ม GitHub Actions Static Checks สำหรับ PHP Syntax และ JavaScript Parse; ยังไม่มี WordPress Runtime, Browser Screenshot, End-to-End Creator Upload, Real License Activation, Live Payment, Ticket Inventory, Seat Locking, DRM หรือ Production Deployment Evidence

**รายการทดสอบก่อนเปิดให้ลูกค้า:**
1. ทดสอบ Plugin Activation และ CPT Capabilities บน WordPress Staging แยกต่างหาก ตรวจสิทธิ์ Anonymous/Subscriber/Admin, REST Auth/Nonce และ Moderation
2. ทดสอบ Mobile Swipe, Desktop Wheel, Keyboard, Reduced Motion, Lazy Loading, Favorites และ Creator Shortcode ผ่าน Browser จริง
3. ทดสอบ ZeaZ License Staging ทั้ง Sign/Issue/Revoke/Expire/Wrong Site และตรวจว่าไม่มี Secret ใน HTML, Git หรือ Application Log
4. ตรวจสอบ Distribution Rights, Content Moderation, Age Rating และข้อกำหนด Privacy ก่อนเปิด Public Site
5. ออกแบบ Studio → Cinema Export เป็น Feature แยก พร้อม Media QC, Human Approval และ Scoped Operator Credentials
6. หากเพิ่ม Ticketing/Payment ให้ใช้ Transactional Inventory, PostgreSQL Seat Holds, Signed Payment Webhooks และการทดสอบ Refund/Concurrency โดยไม่ใช้ WordPress User Meta เป็น Source of Truth

สถานะ: **Source Implemented / Static Validation Pending Runtime Acceptance** ห้ามอ้าง Production-ready จากการ Merge เอกสารหรือ Static CI อย่างเดียว
