# SMB data layout

Recommended Windows share layout:

```text
zmovie/
  source/
  videos/
  exports/
  archive/
  backups/
  evidence/
```

Ubuntu keeps `/var/lib/zmovie` as hot storage. The closeout wrapper currently archives closeout evidence to `evidence/runtime-closeout/<timestamp>` and checksum-verifies it. Completed project media can use `videos`, `exports`, and `archive` through project-aware archival jobs; active render work and SQLite state must stay local.
