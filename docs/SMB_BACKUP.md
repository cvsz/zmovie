# SMB backup role

The Windows SMB tier is a backup/archive destination, not by itself a disaster-recovery guarantee. Keep zMovie's active database and worker state local. Copy generated backup bundles to the SMB `backups/` area and periodically perform a restore drill to temporary local storage. Closeout evidence stored on SMB proves the copy/checksum path, but does not replace a database/media restore test.
