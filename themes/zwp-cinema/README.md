# ZeaZ Cinema — WordPress Theme ของ ZeaZDev (Alpha)

Theme ที่ออกแบบใหม่ในสไตล์โรงภาพยนตร์โทนดำ–ทอง โดยนำเฉพาะแนวคิดการใช้งาน Vertical Video จาก [TikSwipe Feature Page](https://www.wp-script.com/adult-wordpress-themes/tikswipe/) มาเป็น Functional Reference ไม่คัดลอก Source Code, Licensed Assets, Bundle, Logo หรือ Branding ของผู้ผลิต

## ฟีเจอร์ที่พัฒนา

- Fullscreen Vertical Feed พร้อม CSS Scroll Snap สำหรับ Swipe บนมือถือ
- Mouse Wheel, Keyboard Arrow, ปุ่ม Previous/Next และ Video Play/Pause
- โหลดรายการถัดไปผ่าน REST API, Filter ตาม Genre และแสดง Favorites สำหรับผู้ใช้ที่ Login
- หน้า Film Detail พร้อม WordPress Comments, หน้า Creator และหน้า Static Page สำหรับ Shortcode
- รองรับ Custom Logo, Site Icon, WordPress Menu, Responsive Layout และ Reduced Motion

## ติดตั้ง

คัดลอก `themes/zwp-cinema/` ไปยัง `wp-content/themes/zwp-cinema/` แล้ว Activate Theme ควบคู่กับ Plugin `wp-plugins/zwp-cinema/` ใน WordPress Staging เพิ่ม Cinema Film พร้อม MP4/WebM HTTPS URL ที่ได้รับอนุญาต และกำหนด Featured Image เพื่อเป็น Poster สามารถกำหนด Logo, Favicon และ Navigation ผ่าน WordPress Site Identity/Menu

สร้างหน้า `/favorites/` โดยใช้ `[zwpc_favorites]` เพื่อให้เมนู Saved Films แสดงอัตโนมัติ สร้างหน้า Submission ด้วย `[zwpc_submit]` เมื่อพร้อมเปิด Creator Program

**ยังไม่รองรับ:** Ticket Checkout, Premium Paywall, Native File Upload, ระบบสุ่มแบบ Session, Automatic Posters, Script-Based Advertising และ Live Payment ทั้งหมดต้องเป็น Phase แยก พร้อมการตรวจ Security และ Rights

## ทดสอบ

รัน `php -l` ทุกไฟล์ PHP และ `node --check assets/js/reels.js` พร้อมทดสอบจริงใน WordPress Staging บน Mobile, Desktop, Keyboard-Only และ Reduced-Motion ก่อนเปิดใช้งาน Production; ผล Static Check เพียงอย่างเดียวไม่ยืนยันว่าใช้งานจริงได้
