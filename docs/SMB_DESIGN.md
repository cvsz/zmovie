# SMB closeout design

The SMB integration wraps rather than weakens the existing five-gate runtime closeout. Preflight proves the Windows capacity tier is a real writable CIFS/SMB3 filesystem and proves local hot-tier headroom. The existing runtime closeout remains authoritative for deploy, recovery, renderer policy, real-model evidence, and N2N production acceptance. After those gates, evidence is copied to SMB and independently SHA-256 verified. This keeps failures attributable and prevents network storage from becoming a hidden dependency of SQLite or in-progress rendering.
