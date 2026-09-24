# SMB closeout report evidence

`storage-report.json` extends the runtime report with a `storage_tier` object containing the local hot root, SMB mount and archive path, SHA-256 verification state, local free-space snapshot, and storage policy. `SHA256SUMS` is generated from the local evidence set and `SMB_VERIFY.log` records verification against the SMB copy. `STORAGE.txt` records local and SMB filesystem capacity at closeout time.
