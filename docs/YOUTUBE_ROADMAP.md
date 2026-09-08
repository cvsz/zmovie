# YouTube publisher roadmap

Status: **DEFERRED**

YouTube work starts only after the Bilibili production-completion gate is fully evidenced. See [`BILIBILI_PRODUCTION_COMPLETION.md`](BILIBILI_PRODUCTION_COMPLETION.md).

## Intent

The preferred production architecture is **YouTube Data API + OAuth 2.0**, not reuse of a full Chrome browser profile. This minimizes credential exposure and avoids coupling production upload automation to browser selectors.

Planned YouTube phase:

```text
final movie
  -> YouTube metadata package
  -> explicit approval
  -> OAuth 2.0 authorization
  -> upload
  -> thumbnail
  -> playlist assignment
  -> privacy/schedule settings
  -> remote video-ID/public-URL confirmation
  -> durable publish state
```

## Planned controls

- separate YouTube credentials/state from Bilibili browser state;
- OAuth refresh-token storage with least privilege;
- `youtube.upload`-oriented scope selection where practical;
- no Google password or 2FA storage;
- explicit approval before external publication;
- title/description/tag/category validation;
- thumbnail upload;
- playlist support;
- scheduled/private/unlisted/public release controls;
- durable `prepared -> approved -> uploading -> submitted/published/failed` state model;
- remote confirmation using returned YouTube video ID/URL;
- retry/idempotency semantics;
- CI tests with external calls mocked;
- operator runbook and revocation procedure.

## Not started intentionally

No YouTube publisher code, OAuth client flow, token store, API routes, or Studio controls should be implemented until Bilibili reaches the completion definition in `BILIBILI_PRODUCTION_COMPLETION.md`.

This sequencing keeps one external publishing integration under test at a time and prevents cross-platform credential/state handling from expanding before Bilibili is proven end to end.
