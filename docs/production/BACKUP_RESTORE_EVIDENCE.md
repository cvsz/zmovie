# Backup and Restore Evidence

## Backup Configuration
- **Script**: `/opt/backups/wordpress-backup.sh`
- **Cron**: Daily at 2:00 AM (`crontab`)
- **MySQL config**: `/home/cvsz/.my.cnf` (chmod 600)
- **Backup directory**: `/opt/backups/wordpress/`

## Latest Backup
- **File**: `zmovie-cinema-20260924-154646.sql.gz`
- **SHA256**: `6ee1fcb80446a9fd98ffc31dec8f1abb7cab256891cdfb476a67a63d23341b96`
- **Size**: 11K
- **Integrity check**: PASSED

## Isolated Restore Drill
- **Date**: 2026-09-24
- **Restore duration**: 1 second
- **Target database**: `zmovie_cinema_restore` (isolated, not production)
- **Validation results**:
  - Posts: 5 (including Hello world!, Sample Page, Favorites, Submit Film)
  - Users: 1 (zeazadmin)
  - Comments: 1
  - Options: 134
  - Site URL: `https://zmovie.zeaz.dev/cinema` ✅
  - Home URL: `https://zmovie.zeaz.dev/cinema` ✅
  - DB Version: 61833

## Rollback Drill
- **Plugin backup**: `/tmp/zwp-cinema-plugin-backup.tar.gz` (tested and verified)
- **Theme backup**: `/tmp/zwp-cinema-theme-backup.tar.gz` (tested and verified)
- **WordPress routes after rollback**: All responding correctly (200/302)

## Security Fix
- **Issue**: Old DB password `zeaz-cinema-2026` found in backup script
- **Fix**: Replaced with `--defaults-file=/home/cvsz/.my.cnf`
- **New backup script includes**: Integrity check, SHA256 checksum logging
- **Status**: RESOLVED

## Backup Integrity Checks
- Added `zcat` integrity verification to backup script
- Added SHA256 checksum logging to `checksums.txt`
- Automated integrity check on every backup run
