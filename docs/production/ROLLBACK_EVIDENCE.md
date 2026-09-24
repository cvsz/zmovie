# Rollback Evidence — 2026-09-24

> หลักฐาน rollback drill (ภาษาไทย) แยกจาก backup evidence ตามแผน P2

## 1. WordPress plugin/theme rollback

- **Backup:** `tar -czf` ของ `wp-content/plugins/zwp-cinema` และ
  `wp-content/themes/zwp-cinema` ก่อน deploy (ดู runbook §5)
- **Simulate:** แตกไฟล์ backup ลง `/tmp/rollback-test/` ตรวจโครงสร้างครบ
- **Verify:** หลัง rollback `https://zmovie.zeaz.dev/cinema/` 200,
  `/cinema/wp-admin/` 302, `/cinema/wp-json/` 200
- **Cleanup:** ลบไฟล์ชั่วคราวใน `/tmp` แล้ว
- **Result:** SUCCESS

## 2. zMovie code rollback

- **Pre-deploy backup:** `python -m zmovie_platform.runtime_ops backup`
  (SQLite online backup + integrity check + retention ≥ 14)
- **Gate:** `upgrade-readiness` ปฏิเสธ upgrade เมื่อมี worker lease/active
  หรือ publication ค้าง (`claimed/running/recovery_required/submitting`)
- **Rollback:** คืนโค้ด commit เดิม + restore SQLite ตาม
  `docs/BACKUP_AND_RECOVERY.md` + รัน `scripts/smoke-deploy.sh`
- **Result:** กลไกพร้อม (ยังไม่ต้อง rollback จริงในรอบนี้)

## 3. Infra rollback

- `terraform plan` ต้อง zero-destruction ก่อน `apply` ทุกครั้ง
- ถ้า config ผิด: revert commit แล้ว `plan` ใหม่ ห้าม apply ทับ
- Tunnel/DNS source of truth อยู่ใน zworkforce (repo นี้เก็บแค่ example)

## 4. Recovery metrics (ที่วัดได้จริง)

| Metric | Value |
|---|---|
| Isolated WP restore duration | ~1s (11K dump) |
| Backup integrity check | PASS (`zcat` + table presence) |
| Post-rollback route checks | 200/302/200 |
| RTO/RPO ที่ประกาศ | ยังไม่กำหนด — ต้อง operator approval ก่อน (ไม่ invent SLOs) |
