# SMB acceptance criteria

SMB storage is accepted for DBC closeout only when the configured mount resolves to CIFS/SMB3, a write/read/delete probe succeeds, local hot storage remains above the blocking threshold, the five runtime gates execute, evidence copies successfully, and SHA-256 verification succeeds against the SMB copy. A reachable directory alone is not sufficient evidence.
