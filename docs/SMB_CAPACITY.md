# DBC 300 GB local capacity policy

The current 300 GB Ubuntu disk can be retained when Windows SMB carries completed media, exports, archives, backups, and evidence. Local capacity remains the hot tier for OS, zMovie, models currently in use, SQLite/worker state, cache/temp, and active render work. Default closeout thresholds are warning below 60 GB free and blocking below 30 GB free. Capacity should be expanded if the active model set plus worst-case render workspace cannot preserve that headroom.
