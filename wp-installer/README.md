# ZeaZ Cinema — WordPress Auto-Installer

ตัวติดตั้ง WordPress แบบ Self-hosted Local Staging สำหรับ Repository cvsz/zmovie ใช้ Docker Compose, WordPress Official Images, WP-CLI และ MariaDB โดย **ไม่ติดตั้งหรือหลีกเลี่ยง License ของ WP-Script** และไม่แก้ไขระบบ Python zMovie เดิม

## เริ่มต้นใช้งาน (Ubuntu 24.04 / WSL2)

ต้องมี Docker Engine หรือ Docker Desktop พร้อม Docker Compose V2 และ OpenSSL หรือ Python 3 ตัวติดตั้งจะดาวน์โหลด WordPress ZIP จาก WordPress.org ด้วย WP-CLI และตรวจ Checksum โดยเปิดเว็บไซต์เฉพาะ **127.0.0.1:8090**

```bash
git clone https://github.com/cvsz/zmovie.git
cd zmovie
bash wp-installer/install.sh --dry-run
bash wp-installer/install.sh
bash wp-installer/install.sh status
```

เปิดเว็บไซต์ที่ http://127.0.0.1:8090/ และหน้า Admin ที่ http://127.0.0.1:8090/wp-admin/ ชื่อผู้ดูแลและรหัสผ่านเก็บไว้เฉพาะในไฟล์ `wp-installer/.env` ซึ่งตัวติดตั้งสร้างพร้อมตั้งสิทธิ์ไฟล์ 0600 ห้ามเผยแพร่หรือ Commit

ติดตั้งซ้ำด้วย `bash wp-installer/install.sh` ได้โดยไม่ลบ Database ไม่ Reset Admin และไม่เปลี่ยน Theme หรือ Permalink เดิมที่ผู้ดูแลเปลี่ยนเอง แต่ยังตรวจ Core Checksum และเปิดใช้งาน ZeaZ Cinema Plugin หากไม่ได้เปิดอยู่

## สิ่งที่ตัวติดตั้งดำเนินการ

1. สร้าง `.env` จาก `.env.example` และสร้าง Random Secret 256-bit จำนวน 3 ชุดแยกจากกันสำหรับ WordPress Admin, Database User และ Database Root
2. ตรวจ Docker/Compose และยืนยันว่า Port เปิดเฉพาะ Loopback เท่านั้น
3. Pull WordPress PHP 8.3, WP-CLI PHP 8.3, MariaDB 11.4 และ BusyBox; สร้าง Persistent Volumes แยกกันระหว่าง WordPress และ Database
4. ตรวจ MariaDB Health Check แล้วดาวน์โหลด ZIP จาก WordPress.org (ไม่ใช้ TAR Extractor ที่มีปัญหา Path เกิน 100 ตัวอักษร) พร้อม `wp core verify-checksums` เพื่อป้องกัน Core ที่ไม่ตรงกับ WordPress.org
5. สร้าง `wp-config.php`, ติดตั้ง WordPress และ Admin ผ่าน Standard Input แทนการส่ง Password เป็น CLI Argument
6. เปิดใช้ Plugin จาก `wp-plugins/zwp-cinema` และ Theme จาก `themes/zwp-cinema` บนเว็บไซต์ใหม่ พร้อม Permalink `/%postname%/`
7. เปิด Apache และตรวจ Container Health

Plugin และ Theme Mount จาก Repository แบบ Read-only เพื่อทดสอบการพัฒนา ส่วน Uploads และ Database เก็บใน Named Volumes หากจะลบ Volume ต้องทำ Backup/Restore อย่างเป็นระบบ ตัวติดตั้งนี้จงใจไม่มีคำสั่งลบข้อมูล

## ตั้งค่า

สร้างไฟล์ `wp-installer/.env` ผ่านการรันครั้งแรก แล้วแก้ค่าให้เหมาะสมได้ก่อนเปิดใช้งานจริง ตารางค่าหลัก:

| ตัวแปร | ค่าเริ่มต้น | ความหมาย |
| --- | --- | --- |
| `WP_BIND_IP` | `127.0.0.1` | เปิดพอร์ตเฉพาะเครื่อง |
| `WP_PORT` | `8090` | Port ฝั่ง Host |
| `WP_SITE_URL` | `http://127.0.0.1:8090` | Canonical WordPress URL |
| `WP_SITE_TITLE` | ZeaZ Cinema Staging | ชื่อเว็บไซต์ |
| `WP_ADMIN_USER` | `cinema_owner` | Administrator แรก |
| `WP_ADMIN_EMAIL` | `admin@example.invalid` | เปลี่ยนก่อนใช้งาน Public |
| `WP_VERSION` | `latest` | ดาวน์โหลด WordPress เฉพาะเมื่อยังไม่มี Core |
| `WP_LOCALE` | `en_US` | ใช้ `th` เพื่อติดตั้งและเปิดใช้งาน Thai Language Pack หลังติดตั้ง English Core ZIP |
| `WP_DB_NAME` | `zeaz_cinema` | MariaDB แยกจาก zMovie Studio |

หากจะเข้าผ่าน Cloudflare Tunnel ให้ยังคง Bind ที่ 127.0.0.1 และกำหนด Domain, HTTPS, Trusted Proxy และ Forwarded Protocol บน Environment แยกให้ถูกต้องก่อนเริ่มติดตั้ง ตัวติดตั้งจะไม่เปลี่ยน URL ของเว็บไซต์เดิมโดยอัตโนมัติ และ **ยังไม่ใช่ Public Production Deployment Workflow**

## แก้ปัญหา WP-CLI Cache และ PHP Memory

หากเคยพบข้อความ `/.wp-cli/cache/: Permission denied` หรือ `Allowed memory size of 134217728 bytes exhausted` ขณะ Download/Extract WordPress ให้ใช้ Installer จาก Branch ที่รวม Fix นี้ (หรือ Pull Request #18) จากนั้นเรียกคำสั่งติดตั้งเดิมซ้ำโดย **ไม่ลบ Docker Volumes**:

```bash
bash wp-installer/install.sh
```

Installer กำหนด `WP_CLI_CACHE_DIR=/tmp/zeaz-wp-cli-cache` และตั้ง `memory_limit=512M` ให้เฉพาะ WP-CLI ผ่าน `wp-installer/config/wpcli.ini` พร้อมตรวจ Memory Limit ก่อน Download การแก้ไขไม่ต้องให้ Container ทำงานเป็น Root

หากการ Download ครั้งก่อนถูกขัดจังหวะและยังไม่มี `wp-config.php` ตัวติดตั้งจะตรวจ WordPress Core Checksum และ Download ZIP ใหม่เพื่อซ่อมการติดตั้งที่ยังไม่เสร็จ โดยลบเฉพาะ Core AI Client Directory ที่เสียหายจาก TAR Extractor ในการติดตั้งที่ยังไม่ถูก Configure เท่านั้น แต่จะไม่เขียนทับ WordPress ที่ติดตั้งใช้งานอยู่เมื่อ Checksum ผิดพลาด ผู้ดูแลต้องตรวจสอบและสำรองข้อมูลก่อนซ่อม Installation ที่ใช้งานแล้ว

ตรวจ Memory Limit และ Cache ของ WP-CLI:

```bash
docker compose --env-file wp-installer/.env -f wp-installer/compose.yaml run --rm --entrypoint php wpcli -r 'echo ini_get("memory_limit"), PHP_EOL;'
docker compose --env-file wp-installer/.env -f wp-installer/compose.yaml run --rm --entrypoint sh wpcli -c 'printf "%s\n" "$WP_CLI_CACHE_DIR"; mkdir -p "$WP_CLI_CACHE_DIR" && test -w "$WP_CLI_CACHE_DIR"'
```

## การบริหารและข้อจำกัด

```bash
bash wp-installer/install.sh status
bash wp-installer/install.sh stop
bash wp-installer/install.sh
docker compose --env-file wp-installer/.env -f wp-installer/compose.yaml run --rm --entrypoint wp wpcli core verify-checksums
```

Creator Submission แบบ License ยังคงต้องเชื่อมต่อ ZeaZ License Server ตาม [คู่มือ Plugin](../wp-plugins/zwp-cinema/README.md) ตัวติดตั้งนี้ไม่ได้ส่ง Key เข้าระบบของบุคคลที่สาม และไม่ติดตั้ง WP-Script Core หรือ TikSwipe

ยังต้องทดสอบ Backup/Isolated Restore, HTTPS Reverse Proxy, Mail, WAF, Data Protection, Media Rights และ Production Acceptance ก่อนให้ลูกค้าใช้จริง อ้างอิงคำสั่ง [WordPress Download](https://developer.wordpress.org/cli/commands/core/download/), [Core Install](https://developer.wordpress.org/cli/commands/core/install/) และ [Checksum Verification](https://developer.wordpress.org/cli/commands/core/verify-checksums/) จาก WordPress.org
