# Accessibility & Performance Evidence — 2026-09-24

> หลักฐานจริงเท่านั้น (ภาษาไทย) — ไม่เคลม WCAG, ไม่ invent SLO

## 1. Automated accessibility (axe-core, Chromium)

Tool: `@axe-core/playwright` + existing Chromium build. Targets:

| Target | Before | After | Passes |
|---|---|---|---|
| `/cinema/` desktop 1280×800 | 1 serious (`aria-prohibited-attr`) | **0 violations** (38 passes) | ✅ |
| `/cinema/` mobile 390×844 | 1 serious | **0 violations** (38 passes) | ✅ |
| `/membership` desktop | 5 (tested wrong deployment: prod 404 page) | **0 violations** (29 passes) | ✅ |

Fixes (committed + live):
1. `aria-label` on generic feed `<div>` → added `role="feed"`
   (correct semantics for infinite-scroll feed).
2. `role="feed"` requires owned `article` children → conditional role:
   `feed` when films exist, `region` when empty.
3. Membership page content wrapped in `<main>` landmark.

Baseline already present: skip link, nav `aria-label`, button labels,
`aria-pressed`, `role="status"` live regions, image `alt`, Thai `lang`,
`prefers-reduced-motion` CSS, 44px touch targets, bilingual labels.

## 2. Keyboard navigation

- 15× Tab over `/cinema/`: 8 distinct focus stops in logical order
  (skip link → wordmark → nav → pills → genre select), no trap.
- Reduced-motion media query evaluates (no animation to suppress on
  these pages beyond CSS transitions).

## 3. Screen reader (manual procedure — PENDING interactive session)

1. NVDA (Windows) / VoiceOver (macOS) + Chromium/Firefox.
2. `/cinema/`: landmarks (nav/main), feed articles announced with titles,
   buttons announce state (`aria-pressed` on favorites).
3. `/membership`: form labels announced in Thai+English, errors via
   `role="status"`, sandbox banner read as note.
4. Record findings; do not claim coverage until performed.

## 4. Performance baselines (observed, single samples)

| Check | Result |
|---|---|
| `/cinema/` TTFB / DCL / load | 285ms / 513ms / 513ms (n=3) |
| `/cinema/` CLS | 0 (n=3) |
| `/cinema/` LCP | n/a (empty feed, no LCP entry) |
| REST feed (5× public) | median 325ms |
| Staging CRUD create/fetch/delete (loopback) | 52ms / 323ms / 57ms |
| Soak staging health 5×20 loopback | n=100, errors=0, median 359ms, p95 650ms |
| License activate loopback (5×) | median 6ms |
| License health loopback | median 10ms |

Notes: single-worker uvicorn; fetch cost includes QC inspect;
no disruptive public load testing performed.

## 5. Draft SLOs (PROPOSAL — needs operator approval)

| Signal | Proposed objective |
|---|---|
| `/cinema/` TTFB (edge) | p95 < 800ms |
| REST feed (edge) | p95 < 1000ms |
| License activate (origin) | p95 < 500ms |
| Staging health (loopback) | p95 < 1000ms, errors = 0 |
| Checkout success (sandbox) | ≥ 99% excl. user-aborted |

Valid only after 7-day staged measurement + approval. Not commitments.
