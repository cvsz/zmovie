# API authentication

See the [documentation index](../docs/INDEX.md) for canonical guides and
cross-component procedures.

Production API mutation and legacy history/generation routes require
authentication when `ZMOVIE_AUTH_ENABLED=true`; health and login/bootstrap
discovery remain intentionally accessible. HTTP account bootstrap is restricted
to a loopback bind and loopback peer, and the first administrator is inserted
atomically. OAuth account linking requires a provider-verified email; the login
callback redirects to Studio with its token in a URL fragment, which Studio
stores locally and removes from the address bar. Public deployments must set
`ZMOVIE_BASE_URL` to their HTTPS origin so OAuth redirects do not trust the
request's `Host` header. Legacy paths remain for compatibility, while `/studio`
is the primary operator surface.
