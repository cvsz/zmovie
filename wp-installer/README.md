# zMovie WordPress Automated Installer

ตัวติดตั้งนี้ดาวน์โหลด WordPress ผ่าน **WP-CLI**, สร้าง `wp-config.php`, ติดตั้งฐานข้อมูล WordPress และติดตั้ง/Activate `zwp-cinema` Plugin + Theme ของ Repository แบบอัตโนมัติ โดยออกแบบให้รันซ้ำได้และไม่ล้างเว็บไซต์ที่ติดตั้งแล้ว

WP-CLI ใช้คำสั่ง `wp core download` สำหรับดาวน์โหลด WordPress และตรวจ MD5 ของ build ที่ดาวน์โหลด ส่วน `wp core install` จะสร้างตารางมาตรฐานของ WordPress. ตัว installer เปิด `wp core verify-checksums` หลังดาวน์โหลดเป็นค่าเริ่มต้น

## Requirements

Ubuntu/Debian แนะนำ:

```bash
sudo apt update
sudo apt install -y php-cli php-mysql php-curl php-mbstring php-xml php-zip php-sodium \
  curl rsync mariadb-client
```

ต้องมี MySQL/MariaDB ที่เข้าถึงได้จากเครื่องติดตั้ง หาก Database/User ถูก Provision ไว้แล้วให้ใช้ `DB_AUTO_CREATE=false` ซึ่งเป็นค่าเริ่มต้น

## ใช้งาน

```bash
cd ~/zmovie
cp wp-installer/.env.example wp-installer/.env
chmod 600 wp-installer/.env
nano wp-installer/.env

chmod +x wp-installer/install.sh
./wp-installer/install.sh
```

หรือไม่สร้างไฟล์ Secret เลย:

```bash
export WP_PATH=/var/www/zmovie-cinema
export WP_URL=https://cinema.example.com
export WP_TITLE='ZeaZ Cinema'
export WP_ADMIN_USER=zeazadmin
export WP_ADMIN_EMAIL=admin@example.com
export WP_ADMIN_PASSWORD='...secret...'
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DB_NAME=zmovie_cinema
export DB_USER=zmovie_cinema
export DB_PASSWORD='...secret...'

./wp-installer/install.sh
```

## Database Auto-Provisioning

ถ้าต้องการให้ Installer สร้าง Database/User:

```bash
export DB_AUTO_CREATE=true
export DB_ROOT_USER=root
export DB_ROOT_PASSWORD='...database-root-secret...'
```

Installer ใช้ `MYSQL_PWD` เพื่อหลีกเลี่ยงการใส่ Root Password ใน command-line arguments แต่ production host ควรใช้ Secret Manager หรือ MySQL option file ที่ Permission จำกัด

## ZeaZ License

Installer จะเพิ่ม `wp-config.php` constants ที่อ่านค่า License จาก environment โดย **ไม่เก็บ License Key จริงใน Git หรือ wp-config.php**:

- `ZEAZ_LICENSE_API`
- `ZEAZ_LICENSE_ORIGIN`
- `ZEAZ_LICENSE_KEY`
- `ZEAZ_LICENSE_PUBLIC_KEY`

ดังนั้น PHP-FPM/Apache service ต้องได้รับ environment เหล่านี้จากระบบ secrets ของเครื่อง Production

## Idempotency

เมื่อรันซ้ำ:

- ถ้ามี WordPress Core อยู่แล้ว จะไม่ Download ทับ
- ถ้ามี `wp-config.php` จะไม่สร้างใหม่
- ถ้า Database ติดตั้ง WordPress แล้ว จะไม่รัน `core install` ซ้ำ
- Plugin/Theme ของ Repository จะถูก Sync ไปยัง WordPress เพื่อ Update Source ปัจจุบัน
- หน้า `Favorites` และ `Submit Film` จะสร้างเฉพาะกรณีที่ยังไม่มี

หากต้องการ Download Core ทับอย่างชัดเจนให้กำหนด `FORCE_CORE_DOWNLOAD=true`; ไม่ควรใช้กับ Production โดยไม่มี Backup

## Security / Production Gates

- ใช้ HTTPS สำหรับ Public Site และ WP Admin
- ไม่ Commit `.env`; ตั้ง Permission `0600`
- อย่าใช้ Database root account เป็น WordPress runtime account
- ใช้รหัสผ่าน Admin/DB ที่สร้างจาก Secret Manager
- ตรวจ Backup/Restore ก่อน Upgrade
- WordPress Core download/installation สำเร็จไม่ได้แปลว่า `zwp-cinema` ผ่าน Runtime Acceptance แล้ว
- ทดสอบ Plugin/Theme ตาม Checklist ที่ `wp-plugins/zwp-cinema/README.md` ก่อนเปิดลูกค้าจริง
