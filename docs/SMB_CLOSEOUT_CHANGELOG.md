# SMB closeout integration

This change adds a fail-closed Windows SMB capacity tier around the existing five-gate DBC runtime closeout. It does not move active SQLite state, models, or render temp to SMB. The wrapper requires a real CIFS/SMB3 mount, checks local capacity, runs the existing five gates, archives evidence with rsync, and verifies every copied evidence file with SHA-256.

The Windows share address and credentials remain deployment inputs because they are not present in repository configuration and credentials must not be committed.
