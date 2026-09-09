# Authentication implementation

See the [documentation index](../docs/INDEX.md) for canonical guides and
cross-component procedures.

Production auth uses PBKDF2-HMAC-SHA256 password hashing and HMAC-signed expiring bearer tokens. The installer generates the persistent secret and initial admin credentials unless supplied explicitly; an unset secret in direct zero-config development is process-local and is invalidated on restart.
