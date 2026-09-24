# ZeaZ Cinema — first-party WordPress plugin (alpha)

This is original ZeaZDev code for a cinema film catalog and **short-film/trailer feed**. It does not use, copy, modify, activate, or replace WP-Script Core or TikSwipe. WP-Script products that you install separately still require their legitimate upstream product and site licenses.

## Install

1. Copy `wp-plugins/zwp-cinema/` to `wp-content/plugins/zwp-cinema/` in a disposable staging WordPress 6.4+ / PHP 8.1+ installation.
2. Activate **ZeaZ Cinema** in wp-admin and save Settings → Permalinks once.
3. Create a **Cinema Film** (administrator only); set a licensed HTTPS direct MP4/WebM trailer URL and Featured Image. Choose or create a Genre, then publish.
4. Activate the separate first-party `themes/zwp-cinema/` theme from Appearance → Themes.
5. Visit the homepage for the cinematic swipe feed. `/wp-json/zwpc/v1/feed?page=1` returns published films only.

No demo videos, third-party posters or copyrighted media are bundled. Supply footage and artwork you own or are authorized to distribute.

## ZeaZ first-party license for creator submissions

The public film feed, admin curation and read-only film pages do **not** require a license. Front-end creator submission, exposed via a page containing the shortcode `[zwpc_submit]`, is fail-closed unless the server verifies the `cinema.creator` feature from ZeaZ License Server v0.1. The creator must also sign in and confirm distribution rights. Their submission is stored as **pending**, not published.

For staging, issue a first-party `zmovie` license with feature `cinema.creator` in ZeaZ License Server; store the one-time key securely, not in your git repository. Define in your secret-managed WordPress configuration:

```php
define('ZEAZ_LICENSE_API', 'https://license.example.com');
define('ZEAZ_LICENSE_ORIGIN', 'https://cinema.example.com');
define('ZEAZ_LICENSE_KEY', getenv('ZEAZ_LICENSE_KEY'));
define('ZEAZ_LICENSE_PUBLIC_KEY', getenv('ZEAZ_LICENSE_PUBLIC_KEY'));
```

`ZEAZ_LICENSE_PUBLIC_KEY` is the pinned base64url-encoded Ed25519 public key from a trusted out-of-band channel. **Never** copy the signing private key into WordPress or dynamically trust the public key returned by the same activation request. `ZEAZ_LICENSE_ORIGIN` must match the WordPress site origin. API requires HTTPS; local-only HTTP is intentionally not supported by this WordPress plugin until an explicit safe development mode exists.

License leases are verified locally using sodium, audience `zmovie`, site origin, issuer, timestamps and signature. Cached leases expire within 60 seconds. Server-side revocation can be delayed by an already-valid cached lease; do not use this mechanism to authorize payments, payouts, digital-rights grants or booking transactions.

## API and permissions

| Route | Authentication | Behavior |
| --- | --- | --- |
| `GET /wp-json/zwpc/v1/feed?page=1&genre=drama` | Public | Published films, fixed six-item pages |
| `GET /wp-json/zwpc/v1/favorites` | WordPress login | IDs of existing published favorite films |
| `POST /wp-json/zwpc/v1/favorites/{id}` | WordPress login and REST nonce | Toggle user favorite |

Only administrators receive cinema post edit and publish capabilities on activation. Front-end creator submissions are validated through `admin-post.php` with an authenticated session, CSRF nonce, first-party entitlement, HTTPS media URL and rights assertion. Authors cannot self-publish through the default WordPress REST post controller. WordPress accounts, sign-in, comments and profiles use core WordPress functionality.

## Security and limitations

- Do not install this directory inside WP-Script Core or modify `wpscore_site_key`.
- First-party license credentials belong in the host's secrets manager, never WordPress options, README examples with real values, the theme or frontend JavaScript.
- Untrusted external media is **not** downloaded or transcoded by this plugin. Only direct HTTPS MP4/WebM links are accepted; an operator must verify hosting, safety and content rights.
- Native WordPress user meta favorites have last-write-wins behavior under simultaneous writes.
- No live payment gateway, subscription checkout, DRM, ticket inventory, seats, film-rights validation, moderation automation, poster extraction or production deployment evidence is provided in this alpha.
- Before production: review upload/moderation flows, REST API abuse limits, malware scanning for media upload features, age ratings, privacy/consent and offline-license revocation; execute a real WP runtime test on target infrastructure.

## Manual staging acceptance checklist

- [ ] Install on isolated staging WP 6.4+ and PHP 8.1+ with sodium; verify WordPress activation has no notices.
- [ ] Add one licensed direct MP4 trailer and poster; check anonymous feed and keyboard/mobile controls.
- [ ] Assert anonymous users cannot toggle favorites or submit a film.
- [ ] Assert a Subscriber cannot publish via WP REST.
- [ ] Verify valid feature enables submission to pending; expired, revoked or wrong-site lease denies submission.
- [ ] Check incorrect origin/public key rejects all licensed actions; verify no secrets appear in HTML or REST.
- [ ] Confirm WordPress Core comments, menus, archive permalinks and mobile responsive layout.
- [ ] Re-run these checks after adding any payment or membership integration.
