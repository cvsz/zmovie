# SMB fail-closed semantics

The closeout wrapper intentionally fails when `/mnt/zmovie-storage` is not mounted as CIFS/SMB3. This prevents a common failure mode where an unavailable network mount leaves an ordinary local directory behind and archival writes unexpectedly consume the Ubuntu 300 GB disk. A successful path also requires a write/read/delete probe and SHA-256 verification after archival.
