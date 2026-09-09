# API authentication

See the [documentation index](../docs/INDEX.md) for canonical guides and
cross-component procedures.

Production API mutation and legacy history/generation routes require authentication when `ZMOVIE_AUTH_ENABLED=true`; health and login/bootstrap discovery remain intentionally accessible. Legacy paths remain for compatibility, while `/studio` is the primary operator surface.
