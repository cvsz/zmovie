# ZeaZ Cinema WordPress integration — first-party increment

## Scope and vendor separation

Source of inspiration: TikSwipe vendor's public feature page (vertical short video navigation, favorites, user registration, front-end content submission, asynchronous pagination and premium gating), reviewed 2026-09-24. The live demo endpoint did not return retrievable content in the research environment, so this implementation does not claim pixel parity with the demo. No upstream proprietary source, license checks, themes or assets are reused.

New first-party files:
- `wp-plugins/zwp-cinema/`: film CPT, genre taxonomy, public REST feed, authenticated favorites, rights-affirmed moderated creator submission, signed ZeaZ license verifier.
- `themes/zwp-cinema/`: independent black-and-gold WP classic theme; responsive, keyboard-, wheel- and touch-navigable vertical film feed, post details, author page and page template.

The existing `zmovie_platform/` Python render worker, /studio, /product and publication gates are unchanged. Importing zMovie-rendered clips into WordPress is a future *explicitly approved, rights-aware* synchronization boundary. WordPress site owners must provision their own direct HTTPS MP4/WebM assets and posters for this first increment.

## License boundary

The plugin uses the separately implemented first-party ZeaZ License Server (`zmovie` audience) and pinned Ed25519 public key. Premium `cinema.creator` submissions fail closed without a valid signed lease. It never modifies WP-Script Core, `wpscore_site_key`, vendor API calls or vendor entitlement logic. Separate installation of a licensed WP-Script theme/plugin requires the manufacturer's valid Site Key.

## Test evidence and gaps

An isolated PHP syntax / Node parse GitHub Actions workflow checks changed files on PR; it does not run real WordPress or PostgreSQL. No live WordPress deployment, browser screenshot, multi-user license activation, actual creator upload, payment, ticketing, DRM, transactional booking, live feed performance or commercial acceptance test has been completed by creating these source files.

Before enabling paying customers or public publishing:
1. Run WordPress staging runtime acceptance for plugin activation/capabilities, public feed, nonce/auth denials, moderation, creator shortcode/page template, accessible video and favorite behavior on desktop/mobile.
2. Run a ZeaZ License Server integration test with a staged signing key, issue/revoke key, expired token and hostname mismatch. Store secrets out of Git. Confirm revocation response within the documented 60-second cache window.
3. Validate creative rights for every published film; establish content moderation, privacy/cookie documents, user data deletion and film-age rating requirements for target markets.
4. Add optional rights-aware zMovie Studio export to WordPress after media QC and explicit human publication approval, with scoped operator credentials.
5. Separately design cinema showtimes, seat locking, payments and ticket issuance with PostgreSQL transactions and a production-ready PSP. This WordPress teaser feed is not a booking/paywall implementation.
