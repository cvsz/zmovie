# ZeaZ Cinema — first-party WordPress theme (alpha)

Original WordPress cinema theme inspired by generic vertical-video interaction patterns described in the [TikSwipe product features](https://www.wp-script.com/adult-wordpress-themes/tikswipe/): mobile up/down swipe, desktop mouse wheel, keyboard arrows, lazy infinite load, per-user favorites and creator submissions. It intentionally does **not** clone TikSwipe appearance, source code, logos, compiled bundles, screenshots, licensed assets or bundled vendor integrations.

## Features in this increment

- Original dark-gold cinema visual design, responsive full-height reel feed and accessible film details.
- Native CSS scroll snap for swipe, keyboard and desktop wheel shortcuts, playback pauses on inactive video, reduced-motion support.
- REST-based six-item pagination, optional Genre filter and logged-in user favorite controls.
- WordPress custom logo, menus, site icon, sign-in and native comments support.
- HTML escaped and URL-validated public feed; no unapproved ads or third-party tracking injected.

## Install on staging

Copy to `wp-content/themes/zwp-cinema/`, activate alongside `wp-plugins/zwp-cinema/`. For a functional feed, create and publish at least one first-party `Cinema Film` with a licensed trailer MP4/WebM HTTPS link. Set a Featured Image for its poster. Use WordPress Appearance → Menus and Customize → Site Identity to configure the brand and favicon.

The theme does not implement ticket checkout, actual premium paywall, livestream streaming protection, public creator profile editing, image/video uploads, random-per-session ordering, custom advertisement scripts or live payment transactions. All of those are separate, reviewable follow-up releases.

## Verification

`php -l` over every PHP file; `node --check assets/js/reels.js`; WordPress staging browser test on desktop and touch devices; keyboard only and reduced-motion accessibility checks; signed-lease validation on the separately deployed license service. CSS and template presence are **not** evidence of a working live WordPress deployment.
