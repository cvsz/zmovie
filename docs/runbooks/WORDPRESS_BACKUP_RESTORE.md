# WordPress Backup & Restore Runbook (ZeaZ Cinema)

> ขั้นตอนสำรอง/กู้คืน WordPress ภาษาไทย — ห้ามเขียนทับ production DB
> ตรง ๆ โดยไม่ผ่าน isolated restore ก่อน

## 1. ภาพรวม

- **Script:** `/opt/backups/wordpress-backup.sh` (mysqldump + gzip + wp-content tar + SHA256 + integrity check)
- **Cron:** ทุกวัน 02:00 (`0 2 * * * /opt/backups/wordpress-backup.sh`)
- **MySQL auth:** `--defaults-file=/home/cvsz/.my.cnf` (chmod 600) — ห้ามใช้ `--password=` บน CLI
- **ปลายทาง:** `/opt/backups/wordpress/zmovie-cinema-<TIMESTAMP>.sql.gz` + `wp-content-<TIMESTAMP>.tar.gz` + `checksums.txt`
- **System cron WP:** ทุก 5 นาที `wp cron event run --due-now` (แทน WP-CRON ผ่าน web)

## 2. สำรองข้อมูลด้วยมือ (ก่อน deploy/upgrade ทุกครั้ง)

```bash
sudo /opt/backups/wordpress-backup.sh
ls -lah /opt/backups/wordpress/zmovie-cinema-*.sql.gz | tail -3
```

ต้องเห็น `SHA256:` และ `Integrity check passed` จึงถือว่าสำเร็จ

## 3. ตรวจความสด/สมบูรณ์อัตโนมัติ (สำหรับ monitoring)

```bash
bash scripts/check-backup.sh
```

- exit 0 = มี backup ใหม่กว่า 26 ชม. + gzip แกะได้ + มีตาราง `wp_posts/wp_users/wp_options`
- exit ≠ 0 = ส่ง alert (ตั้ง cron พร้อม `MAILTO=` หรือ webhook ภายนอก)

## 4. Isolated restore (บังคับก่อนแตะ production)

```bash
LATEST=$(ls -t /opt/backups/wordpress/zmovie-cinema-*.sql.gz | head -1)
sha256sum "$LATEST"
sudo mysql -u root -e "CREATE DATABASE IF NOT EXISTS zmovie_cinema_restore;"
zcat "$LATEST" | sudo mysql -u root zmovie_cinema_restore
sudo mysql -u root -D zmovie_cinema_restore -e "SHOW TABLES; SELECT COUNT(*) FROM wp_posts;"
sudo mysql -u root -D zmovie_cinema_restore -e "SELECT option_name,option_value FROM wp_options WHERE option_name IN ('siteurl','home');"
```

เกณฑ์ผ่าน: ตารางครบ, `siteurl`/`home` = `https://zmovie.zeaz.dev/cinema`,
นับ `wp_posts/wp_users` ตรงกับ production, เปิด staging แยกแล้ว boot ได้

## 5. Rollback plugin/theme (known-good code)

```bash
sudo tar -czf /tmp/zwp-cinema-plugin-backup.tar.gz -C /var/www/zmovie-cinema wp-content/plugins/zwp-cinema
sudo tar -czf /tmp/zwp-cinema-theme-backup.tar.gz -C /var/www/zmovie-cinema wp-content/themes/zwp-cinema
# ... deploy โค้ดใหม่ ...
# ถ้าพัง: แตกไฟล์ backup ทับ แล้วตรวจ routes
curl -s -o /dev/null -w '%{http_code}\n' https://zmovie.zeaz.dev/cinema/
curl -s -o /dev/null -w '%{http_code}\n' https://zmovie.zeaz.dev/cinema/wp-json/
```

## 6. ข้อห้าม

- ห้าม restore ทับ `zmovie_cinema` (production) โดยไม่มี isolated restore ผ่านก่อน
- ห้าม commit/print/share secret (`DB_PASSWORD`, `.my.cnf`, license keys)
- ห้ามใช้ `--password=` บน command line (เห็นใน `ps`)
- staging กับ production ต้องแยก DB/ไฟล์/hostname เสมอ

## 7. หลักฐานล่าสุด

ดู `docs/production/BACKUP_RESTORE_EVIDENCE.md` (restore drill 1 วินาที,
ข้อมูลครบ, rollback สำเร็จ)
