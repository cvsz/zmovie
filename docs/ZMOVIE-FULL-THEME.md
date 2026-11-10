# ZMOVIE — UNIVERSAL ENTERPRISE ADMIN DASHBOARD MASTER PROMPT
## AdminLTE-Inspired Full Independent Implementation

PROJECT: zMovie
REPOSITORY: https://github.com/cvsz/zmovie
DESIGN REFERENCE: https://github.com/ColorlibHQ/AdminLTE
PRIMARY BRANCH: main
APPLICATION: AI Movie Production and Content Automation Platform

MISSION:

Independently audit, design, implement, integrate, upgrade, test, secure, and complete the zMovie Enterprise Admin Dashboard.

Build a professional Production Control Center inspired by AdminLTE.

This is a full implementation assignment. Do not stop at design recommendations, screenshots, mockups, static HTML, or documentation.

Implement the actual working application using the existing repository architecture and backend APIs.

The dashboard must provide unified operational visibility and control over every supported zMovie subsystem.

---

# 0. NON-NEGOTIABLE REPOSITORY RULES

Read and obey:

- AGENTS.md
- README.md
- SECURITY.md
- CONTRIBUTING.md
- docs/INDEX.md
- docs/ARCHITECTURE.md
- docs/API.md
- docs/OPERATIONS.md
- docs/TESTING.md
- docs/STATUS.md
- docs/CONFIGURATION.md
- docs/RUNTIME_EVIDENCE.md
- docs/LONG_RUNNING_RENDER_WORKER.md
- docs/BACKUP_AND_RECOVERY.md
- docs/BILIBILI_PUBLISHING.md
- docs/BILIBILI_PRODUCTION_COMPLETION.md
- docs/production/CURRENT_STATE.md
- docs/production/FEATURE_MATRIX.md

Also inspect:
- `zmovie_platform/README_API_V2.md`
- `zmovie_platform/README_API_AUTH.md`
- `zmovie_platform/README_WORKERS.md`
- `zmovie_platform/README_SECURITY.md`
- `zmovie_platform/README_OBSERVABILITY.md`
- `zmovie_platform/zeazverse/`
- `docs/kids-factory/`

Repository instructions have precedence over this prompt when they establish a more restrictive safety or security boundary.

Communication and documentation must follow repository language requirements: Thai for human-facing explanations and documentation; English for source code, identifiers, routes and configuration.

Preserve existing architecture, contracts, functionality and backward compatibility.

Do not remove existing functionality to simplify the dashboard.

Do not create a third application or a parallel backend without demonstrating a necessary architectural reason.

---

# 1. REPOSITORY BASELINE AUDIT

Inspect the complete repository.

Core application:
- `app.py`
- `main.py`
- `zmovie.py`
- `zmovie_platform/`

Current frontend:
- `static/index.html`
- `static/style.css`
- `static/app.js`
- `static/studio.html`
- `static/studio-preview.js`
- `static/product.html`
- `static/product.css`
- `static/product.js`
- `static/durable-worker.js`
- `static/hyperframes-studio.js`
- `static/membership.html`
- `static/membership.js`

Backend modules:
- `api_routes.py`
- `api_schemas.py`
- `auth.py`
- `audit.py`
- `health.py`
- `metrics.py`
- `runtime.py`
- `runtime_ops.py`
- `worker.py`
- `worker_queue.py`
- `production.py`
- `storyboard.py`
- `content_storyboard.py`
- `media.py`
- `media_pipeline.py`
- `media_preview.py`
- `media_upload_routes.py`
- `product_routes.py`
- `product_video.py`
- `publisher_routes.py`
- `publishers/`
- `kids_factory.py`
- `kids_routes.py`
- `zeazverse/`
- `zflow.py`
- `commerce/`
- `studio_cinema.py`
- `privacy.py`
- `privacy_routes.py`

Infrastructure:
- Dockerfile
- docker-compose.yml
- install.sh
- install-docker.sh
- deploy/
- scripts/
- systemd service definitions
- backup and restore scripts
- GitHub workflows

Inspect every existing dashboard-related route, API contract, JavaScript module, stylesheet, and test before deciding the implementation strategy.

Produce a baseline matrix showing:
- Existing functionality.
- Existing UI.
- API readiness.
- Authentication requirements.
- Permissions.
- Data source.
- Test coverage.
- Missing capability.
- Risk level.

Do not infer live operational status from old documentation or previously generated reports. Verify current code and runtime evidence separately.

---

# 2. DESIGN SYSTEM — ADMINLTE-INSPIRED ZMOVIE

Reference: https://github.com/ColorlibHQ/AdminLTE

Review the current AdminLTE release and choose a compatible, maintained implementation approach.

Do not assume version-specific APIs or dependencies.

Inspect the repository license and any assets before reuse.

Implement an original zMovie visual identity using AdminLTE-inspired dashboard patterns.

## 2.1 Visual direction

Style:
- Premium professional media-production SaaS.
- Dark charcoal sidebar.
- Clean light content surface.
- Optional dark theme.
- Professional blue primary actions.
- Restrained status colors.
- High-quality media thumbnails.
- Clear status indicators.
- Consistent information hierarchy.
- Compact but readable operational density.

Design should feel suitable for a professional creative-production team.

Avoid excessive gradients, oversized hero content, decorative animations and unnecessary card nesting.

## 2.2 Design tokens

Create centralized tokens for:
- Color.
- Typography.
- Spacing.
- Border radius.
- Elevation.
- Shadows.
- Status colors.
- Breakpoints.
- Z-index.
- Motion.
- Chart palette.

Support:
- Light theme.
- Dark theme.
- Theme persistence.
- Accessible contrast.
- Reduced-motion preference.

## 2.3 Application shell

Build:

A. Sidebar:
- Brand logo.
- Collapsible state.
- Nested sections.
- Active route indicator.
- Navigation badges.
- Tooltips in collapsed mode.
- Mobile off-canvas behavior.
- Permission-aware navigation.

B. Navbar:
- Sidebar toggle.
- Breadcrumbs.
- Global search.
- Notifications.
- System status.
- User menu.
- Theme switch.
- Quick-create actions.

C. Content:
- Page title.
- Breadcrumb.
- Description.
- Action toolbar.
- Responsive grid.
- Cards.
- Tables.
- Forms.
- Charts.
- Status feedback.

D. Footer:
- Application version.
- Environment.
- API health.
- Worker availability.
- Latest successful synchronization time.

Status values must come from actual APIs.

---

# 3. COMPLETE INFORMATION ARCHITECTURE

Implement routes based on verified functionality.

## 3.1 Main Dashboard

Route: `/admin`

Executive production overview.

KPI cards:
- Total projects.
- Active projects.
- Production runs.
- Active worker jobs.
- Completed renders.
- Failed jobs.
- Assets produced.
- Pending QC.
- Pending approvals.
- Published media.
- Storage utilization.
- Recent production cost when reliably available.

Dashboard charts:
- Production jobs over time.
- Render success/failure ratio.
- Queue depth.
- Average render duration.
- Worker utilization.
- Provider distribution.
- Media production volume.
- Publication status.

Recent activities:
- Project created.
- Storyboard generated.
- Render queued.
- Render completed.
- QC rejected.
- Export completed.
- Approval submitted.
- Publication confirmed.
- Worker recovered.

Every metric must include a valid source, unit and timestamp.

Never show fabricated production statistics as live data.

## 3.2 Production Studio

Route: `/admin/studio`

Integrate the existing `/studio` application.

Features:
- Project browser.
- Project creation.
- Content brief.
- Storyboard.
- Character Bible.
- Scene management.
- Shot management.
- Continuity checks.
- Production readiness.
- Render configuration.
- Production runs.
- Asset previews.
- Run status.
- Error diagnosis.
- Export and handoff.

Preserve the existing production workflow.

Do not replace its established functionality with dashboard-only placeholders.

## 3.3 Product Video Studio

Route: `/admin/products`

Integrate the existing `/product` application.

Features:
- Product catalog.
- Product details.
- Brand.
- Category.
- Audience.
- Features.
- Benefits.
- Pricing.
- Currency.
- Creative direction.
- Suitability scoring.
- AI production plan.
- Prompt generation.
- Storyboard handoff.
- Production history.

Product claims must be grounded in the provided product evidence.

Never manufacture unsupported product claims, prices, discounts or endorsements.

## 3.4 Project Management

Route: `/admin/projects`

Implement:
- Projects list.
- Project details.
- Status.
- Owner.
- Created date.
- Last modified.
- Production progress.
- Character relationships.
- Scene count.
- Shot count.
- Assets.
- Run history.
- Search and filters.
- Pagination.
- Ownership enforcement.

Support safe project archival only if the backend defines the operation.

## 3.5 Storyboards

Route: `/admin/storyboards`

Implement:
- Storyboard list.
- Scene sequence.
- Shot sequence.
- Character continuity.
- Scene duration.
- Camera direction.
- Visual prompt.
- Negative prompt.
- Voice-over.
- Soundtrack cues.
- Storyboard version history.
- Continuity validation.
- Timeline checksum.

Display validation failures without automatically changing the approved storyboard.

## 3.6 Character Bible

Route: `/admin/characters`

Implement:
- Character catalog.
- Character details.
- Reference images.
- Visual identity.
- Personality.
- Voice profile.
- Continuity rules.
- Locked attributes.
- Version history.
- Character usage across projects.

Support ZEAZVERSE character profiles.

Never infer consent for voice cloning or impersonation.

Use verified permissions and consent records from the backend.

## 3.7 Render Queue

Route: `/admin/queue`

This is a critical operations page.

Implement:
- Pending jobs.
- Running jobs.
- Completed jobs.
- Failed jobs.
- Retrying jobs.
- Worker leases.
- Heartbeats.
- Attempt count.
- Retry schedule.
- Provider.
- Remote prompt identity.
- Job age.
- Queue depth.
- Priority where supported.
- Worker assignment.
- Error details.

Controls:
- Pause queue.
- Resume queue.
- Cancel job when safely supported.
- Retry according to backend policy.
- Inspect job.
- Inspect recovery history.

All actions must use existing authorized backend endpoints.

Never implement queue mutation directly in browser JavaScript or by writing SQLite.

## 3.8 Worker Operations

Route: `/admin/workers`

Implement:
- Worker inventory.
- Worker health.
- Heartbeat.
- Active lease.
- Job assignment.
- CPU/RAM metrics.
- GPU availability.
- Vulkan device information.
- Render backend.
- Provider health.
- Worker errors.
- Recovery activity.
- Worker version.

Support:
- Native systemd worker.
- Docker deployment.
- Remote ComfyUI integration.
- stable-diffusion.cpp CPU/Vulkan.

Distinguish application health from actual GPU/model readiness.

Do not label a worker GPU-ready based only on device detection.

Do not restart a worker simply because a model is missing.

## 3.9 AI Providers

Route: `/admin/providers`

Implement:
- Provider inventory.
- Provider category.
- Configuration presence.
- Health.
- Availability.
- Capability.
- Model metadata.
- Timeout.
- Queue latency.
- Provider errors.
- Last successful operation.

Support only verified provider integrations:
- ComfyUI.
- stable-diffusion.cpp.
- Generic HTTP gateway.
- Other adapters found in the actual repository.

Never expose provider tokens or credential values.

Distinguish configured, connected, tested and production-verified provider states.

The mock provider must be explicitly marked as a dry-run/test provider and rejected as production AI evidence.

## 3.10 Render Jobs and Media

Routes:
- `/admin/renders`
- `/admin/media`

Implement:
- Render jobs.
- Output assets.
- MP4 previews.
- Thumbnails.
- Audio.
- Image assets.
- Metadata.
- Duration.
- Resolution.
- Frame rate.
- Codec.
- File size.
- Hash.
- Storage location metadata.
- Asset relationships.
- Preview history.
- Export history.

Use managed short-lived media preview URLs.

Never accept arbitrary filesystem paths from browser requests.

Do not expose internal storage paths.

Support:
- Search.
- Type filter.
- Project filter.
- Date filter.
- Preview.
- Download with authorization.
- Safe deletion only where explicitly supported.

## 3.11 Quality Control

Route: `/admin/qc`

Implement:
- QC overview.
- Media validation.
- FFprobe results.
- Duration verification.
- Resolution.
- Frame integrity.
- Audio verification.
- Continuity checks.
- Required asset validation.
- Manifest validation.
- ML score where supported.
- Production readiness.

Clearly distinguish:
- Passed.
- Failed.
- Warning.
- Blocked.
- Pending.
- Not tested.

A successful mock render must never pass the real-media production gate.

A project must not become production-ready merely because an AI score is high.

## 3.12 Timeline and Assembly

Route: `/admin/timeline`

Implement:
- Scene timeline.
- Shot timeline.
- Asset assignment.
- Duration.
- Transitions.
- Audio tracks.
- Subtitle tracks.
- Assembly configuration.
- FFmpeg assembly status.
- Final validation.
- Versioned exports.

Use existing Hyperframes and assembly integrations.

Do not build a complete non-linear editing engine unless a real product requirement and technical specification justify it.

## 3.13 Exports

Route: `/admin/exports`

Implement:
- Export jobs.
- ZIP package.
- Manifest.
- Production assets.
- Media integrity.
- File hash.
- Creation date.
- Download status.
- Expiration where applicable.
- Audit trail.

Downloads must be authorization-checked.

## 3.14 Publication Center

Route: `/admin/publishing`

Implement Bilibili publishing operations:

- Creator Center session status.
- Publication candidates.
- Publication package.
- Exact package hash.
- Metadata.
- Cover.
- Description.
- Tags.
- Content category.
- Schedule.
- Approval.
- Preflight.
- Submission state.
- Public URL.
- Remote confirmation.
- Publication history.
- Audit evidence.

Maintain the exact workflow:

PREPARED
→ HUMAN APPROVAL
→ PREFLIGHT
→ EXPLICIT SUBMISSION
→ REMOTE CONFIRMATION
→ PUBLISHED

Critical safeguards:

1. `ZMOVIE_BILIBILI_AUTO_PUBLISH=false` remains the default.
2. Publishing must never be triggered by render completion.
3. Exact-package approval must bind to the exact package version/hash.
4. Approval cannot be reused for a changed package.
5. Do not blindly retry ambiguous external submission.
6. `submitted` does not mean `published`.
7. A genuine public URL and remote confirmation are required for publication completion.
8. The dashboard must not manufacture successful publication status.
9. Google passwords and 2FA secrets must never be requested or stored.
10. Browser session state is a sensitive credential and must remain protected.

All external publication actions require explicit human authorization.

## 3.15 ZEAZVERSE

Route: `/admin/zeazverse`

Integrate the existing virtual idol and multi-agent production domain.

Implement:
- Channel overview.
- Character Bible.
- Episode management.
- Agent inventory.
- Agent execution status.
- Scriptwriting.
- Storyboards.
- Cinematography.
- Video production.
- Audio production.
- Editing.
- Continuity QA.
- SEO.
- Policy and rights review.
- Publishing workflow.
- Analytics.
- Human approval gates.

Represent the canonical episode state machine accurately.

Do not independently implement another workflow engine.

All agents must obey the current backend contracts and publishing permissions.

## 3.16 Kids Content Factory

Route: `/admin/kids`

Integrate `/api/v2/kids/*`.

Implement:
- Brands.
- Channels.
- Characters.
- Episodes.
- Scripts.
- Scenes.
- Timeline.
- Voice profiles.
- Consent validation.
- Music license validation.
- Captions.
- Language variants.
- Educational objectives.
- Safety analysis.
- Publishing metadata.
- Cost estimation.

Strict safety requirements:
- Preserve COPPA-related controls.
- Preserve age-appropriate content gates.
- Do not weaken prohibited-content checks.
- Preserve made-for-kids classification.
- Preserve synthetic-content disclosures.
- Enforce voice cloning consent.
- Do not expose child personal data unnecessarily.
- Keep YouTube mock publishing distinct from real publication.

## 3.17 Cinema and WordPress

Route: `/admin/cinema`

Integrate the existing:
- ZeaZ Cinema plugin.
- ZeaZ Cinema theme.
- WordPress feed integration.
- Moderated creator submissions.
- Favorites.
- Film catalog.
- Creator pages.
- Licensing workflows.

Keep Studio, Cinema, Commerce and ticketing domain boundaries intact.

Do not bypass the two required human approvals in the Studio-to-Cinema boundary.

Do not automatically publish completed renders to WordPress.

## 3.18 Commerce and Membership

Routes:
- `/admin/commerce`
- `/admin/membership`
- `/admin/licenses`

Inspect existing commerce, ticketing, license and membership routes.

Implement only capabilities supported by actual backend contracts.

Support:
- Product/catalog information.
- Membership.
- Subscription status where implemented.
- License status.
- Orders.
- Payment status.
- Entitlements.
- Ticketing where implemented.
- Operational audit.

Never display payment success without backend confirmation.

Never expose payment secrets or full sensitive payment identifiers.

Keep financial transactions separate from video publication approval.

## 3.19 Analytics

Route: `/admin/analytics`

Implement:
- Project throughput.
- Production completion rate.
- Render success rate.
- Render failure rate.
- Average render time.
- Queue wait time.
- Worker availability.
- Provider performance.
- Storage usage.
- Media volume.
- QC pass rate.
- Export history.
- Publication conversion.
- Cost analytics where actual cost data exists.

Charts should include:
- Time-series line.
- Bar charts.
- Donut charts.
- Provider comparison.
- Production funnel.
- Queue activity.

Use real aggregation APIs or introduce tested backend read models.

Never invent cost or usage metrics.

## 3.20 System Health

Route: `/admin/system`

Implement:
- API.
- Database.
- Worker.
- Queue.
- ComfyUI.
- stable-diffusion.cpp.
- FFmpeg.
- GPU/Vulkan.
- Storage.
- Backup.
- Watchdog.
- Scheduler.
- External service dependencies.

Show:
- Current state.
- Last check.
- Response time.
- Error.
- Last successful operation.
- Diagnostic link.

## 3.21 Audit and Security

Routes:
- `/admin/audit`
- `/admin/security`

Implement:
- Audit log.
- Actor.
- Action.
- Entity.
- Timestamp.
- Request ID.
- Result.
- Evidence hash.
- Security event.
- Authentication event.
- Authorization denial.
- Session activity.
- Sensitive operation history.

Audit records must be immutable through the dashboard.

Do not reveal session tokens, secrets or sensitive request bodies.

## 3.22 Administration

Routes:
- `/admin/users`
- `/admin/roles`
- `/admin/settings`
- `/admin/integrations`
- `/admin/preferences`

Implement only actual supported backend permissions and operations.

Never use hidden frontend links as a security boundary.

Every sensitive action requires server-side authorization.

---

# 4. API INTEGRATION

Use the real existing FastAPI backend.

Inspect the current API contracts from code and the deployed API's OpenAPI specification when available.

Important existing route groups include:

Platform:
- `/api/health`
- `/api/v2/health`
- `/api/v2/capabilities`
- `/api/v2/analytics/overview`

Authentication:
- `/api/v2/auth/login`
- Existing session and OAuth routes.

Projects:
- `/api/v2/projects`

Content:
- `/api/v2/content/storyboard`
- `/api/v2/content/storyboard/analyze`

Product:
- `/api/v2/products/plan`
- `/api/v2/products/analyze`

Production:
- `/api/v2/projects/{id}/production/readiness`
- `/api/v2/projects/{id}/production/render`
- `/api/v2/projects/{id}/production/run`
- `/api/v2/projects/{id}/production/runs/{run_id}`
- `/api/v2/projects/{id}/production/runs/{run_id}/deep-status`
- `/api/v2/projects/{id}/production/assemble`
- `/api/v2/projects/{id}/production/export`

Worker:
- `/api/v2/worker/status`
- `/api/v2/worker/jobs/{worker_job_id}`
- `/api/v2/worker/performance`

Publication:
- `/api/v2/publish/bilibili/session`
- `/api/v2/projects/{id}/publish/bilibili/prepare`
- `/api/v2/publish/jobs/{id}/approve`
- `/api/v2/publish/jobs/{id}/publish`
- `/api/v2/publish/jobs/{id}`
- `/api/v2/publish/jobs/{id}/audit-trail`

Other domains:
- `/api/v2/kids/*`
- Commerce and ticketing routes.
- Media upload and preview.
- Privacy.
- ZEAZVERSE.
- Cinema integration.
- Legacy prompt generation and history.

Do not assume that these examples cover all routes or describe exact payload shapes.

Verify each endpoint and schema before connecting UI controls.

## API client

Implement a typed API layer with:
- Centralized base URL.
- Authentication.
- CSRF.
- Timeouts.
- Request cancellation.
- Structured errors.
- Response validation.
- Pagination.
- Filtering.
- Correlation IDs.
- Safe retries for idempotent reads.
- Cache invalidation.
- Version compatibility.

Do not retry non-idempotent production or publishing actions blindly.

Do not store access tokens in unsafe browser persistence.

Keep secrets server-side.

---

# 5. REAL-TIME OPERATIONS

Inspect existing WebSocket and event transport implementations.

Implement real-time operational updates for:
- Queue.
- Worker heartbeat.
- Job status.
- Render progress.
- Production stages.
- QC.
- Exports.
- Notifications.
- Publishing state.

Requirements:
- Connection management.
- Bounded exponential retry.
- Stale connection detection.
- Heartbeats.
- Event ordering.
- Duplicate event protection.
- Reconnect reconciliation.
- Subscription cleanup.
- Visibility-aware updates.

A reconnect must reconcile current state with the authoritative backend.

Never infer a completed job from a missing heartbeat.

---

# 6. FORM ENGINEERING

Implement reusable forms with:
- Typed field schemas.
- Validation.
- Field-level errors.
- Error summaries.
- Loading states.
- Confirmation.
- Cancel.
- Server error handling.
- Accessible descriptions.
- Success feedback based on server confirmation.

Required forms:
- Create project.
- Edit project metadata.
- Create storyboard.
- Product analysis.
- Production configuration.
- Render submission.
- Queue action confirmation.
- Provider configuration.
- QC review.
- Export request.
- Publication package.
- Publication approval.
- Publishing preflight.
- User preferences.
- Membership and commerce settings where supported.

Dangerous and externally visible actions must require explicit confirmation.

Never allow the user interface to bypass backend state machines.

---

# 7. MEDIA-FIRST UX

zMovie is a cinematic production application.

The visual experience must prioritize actual production media.

Implement:
- Poster grids.
- Project cards.
- Storyboard galleries.
- Character reference galleries.
- Video preview.
- Audio preview.
- Asset viewer.
- Scene timeline.
- Production progress.
- Media detail drawers.
- Export packages.

Video playback must use managed, authorized preview URLs.

Handle unsupported codecs, expired URLs, deleted assets and failed downloads gracefully.

Provide image/video loading skeletons.

Do not use arbitrary filesystem paths or long-lived public storage URLs.

---

# 8. RESPONSIVE COMPONENTS

Build reusable components:

Layout:
- AdminAppShell
- AdminSidebar
- AdminNavbar
- AdminBreadcrumb
- PageHeader
- PageToolbar
- ContentGrid

Widgets:
- InfoBox
- SmallBox
- StatCard
- StatusCard
- ActivityTimeline
- SystemHealthCard
- QueueSummary

Media:
- ProjectCard
- VideoPlayer
- MediaGallery
- AssetCard
- CharacterCard
- StoryboardCard
- TimelineView

Data:
- DataTable
- Pagination
- SearchFilter
- DateFilter
- StatusBadge
- EmptyState
- ErrorState
- LoadingSkeleton

Production:
- ProductionProgress
- RenderJobCard
- WorkerCard
- ProviderCard
- QcReport
- ApprovalPanel
- PublicationTimeline

Forms:
- FormField
- FormSection
- ValidationSummary
- ConfirmDialog
- ActionMenu

Avoid redundant abstractions.

---

# 9. AUTHENTICATION AND AUTHORIZATION

Use the existing auth implementation and documented session contracts.

Implement:
- Secure login.
- Logout.
- Session expiration.
- OAuth where supported.
- Permission-aware navigation.
- Protected routes.
- Project ownership.
- Role-based controls.
- CSRF protection.
- Audit logging.

Never trust frontend role data without backend authorization.

Never expose:
- Admin bootstrap password.
- Signing secret.
- OAuth client secret.
- Provider tokens.
- Bilibili storage state.
- Google credentials.
- 2FA secrets.
- Arbitrary filesystem locations.

Do not place private secrets into localStorage, sessionStorage, query strings, telemetry, screenshots or logs.

Use short-lived, scoped media URLs.

---

# 10. SAFETY AND HUMAN APPROVAL BOUNDARIES

These constraints override dashboard requirements.

## Production rendering

A render action must:
1. Verify project ownership.
2. Validate production configuration.
3. Verify provider readiness.
4. Pass backend production gates.
5. Enqueue durable work.
6. Return the authoritative job identifier.
7. Reconcile status from the queue.

Do not execute multi-hour AI inference inside a FastAPI request handler.

## Production media

A production media asset must pass strict FFprobe and assembly validation.

The mock provider is dry-run only.

Never label mock output as production media.

## External publishing

A render must never automatically publish externally.

Maintain exact-package human approval.

Maintain explicit submission confirmation.

Handle ambiguous external state without blind retries.

Published status requires genuine remote confirmation.

## Kids content

Preserve all age-appropriate content, privacy, COPPA-related, classification and consent boundaries.

Do not weaken deterministic safety checks for UI convenience.

## Commerce

All financial actions require backend authorization and transaction confirmation.

---

# 11. PERFORMANCE

Implement:
- Route-level code splitting.
- Lazy-loaded charts.
- Media lazy loading.
- Efficient DOM updates.
- Pagination.
- Server-side filtering.
- Request cancellation.
- Bounded event subscriptions.
- Efficient image previews.
- Avoidance of unnecessary polling.
- Memory leak prevention.

Target:
- No horizontal overflow.
- Responsive mobile navigation.
- Fast page transitions.
- No duplicate real-time subscriptions.
- Stable video previews.
- Controlled chart update frequency.

Measure actual performance rather than claiming improvements without evidence.

---

# 12. ACCESSIBILITY

Target WCAG 2.2 AA.

Implement:
- Semantic elements.
- Accessible navigation.
- Keyboard operation.
- Visible focus.
- Dialog focus management.
- Accessible forms.
- Descriptive errors.
- Screen reader status.
- Sufficient contrast.
- Reduced motion.
- Accessible chart summaries.
- Captions/subtitle metadata where available.

Never communicate status using color alone.

---

# 13. OBSERVABILITY

Integrate with existing metrics and diagnostics.

Track:
- Dashboard load performance.
- API failures.
- Request latency.
- Render job updates.
- Queue refresh errors.
- Worker connection.
- Media preview errors.
- Authentication failures.
- Publication state errors.
- Frontend exceptions.

Include correlation IDs.

Do not log credentials or media-access tokens.

---

# 14. TESTING

Use the repository's existing test ecosystem.

Backend:
- Python unittest and pytest where configured.
- FastAPI TestClient.
- Existing integration tests.

Frontend:
- JavaScript syntax checks.
- Existing Studio/Product compatibility checks.
- Playwright where configured.
- Browser-based responsive testing.

Required scenarios:

1. Admin login.
2. Invalid credentials.
3. Unauthorized access.
4. Session expiration.
5. Project listing.
6. Project creation.
7. Storyboard viewing.
8. Product analysis.
9. Render queue.
10. Worker status.
11. Worker heartbeat loss.
12. Render failure.
13. Render recovery.
14. Media preview authorization.
15. QC failure.
16. Export download.
17. Bilibili package preparation.
18. Approval for the exact package.
19. Changed package invalidates prior approval.
20. Ambiguous submission state.
21. Genuine publication confirmation.
22. Kids safety rejection.
23. Consent validation.
24. Theme preference.
25. Mobile navigation.
26. Empty states.
27. Backend unavailable.
28. Duplicate real-time events.
29. Real-time reconnect.
30. No secret disclosure in browser or logs.

Test both success and failure paths.

Mock external rendering and publishing in normal CI.

Do not perform real external publication during automated tests.

---

# 15. SECURITY AUDIT

Perform a dedicated audit covering:

- Authentication bypass.
- Authorization bypass.
- CSRF.
- XSS.
- SQL injection.
- Path traversal.
- SSRF.
- Open redirect.
- Media URL leakage.
- Insecure file access.
- Session fixation.
- Unsafe browser storage.
- Credential leakage.
- Missing rate limits.
- Unsafe upload handling.
- ZIP extraction traversal.
- Content metadata injection.
- Publication approval reuse.
- Duplicate publication.
- Queue race conditions.
- Unsafe filesystem permissions.
- Backup exposure.
- Worker privilege escalation.
- Untrusted external data.

Preserve existing security controls.

Do not disable checks or loosen policy to achieve successful tests.

Record unresolved risks explicitly.

---

# 16. DEPLOYMENT

Support both documented deployment modes:

A. Native systemd:
- Existing FastAPI service.
- Dedicated worker.
- Watchdog.
- Backup timer.
- Persistent application data.

B. Docker:
- Existing Docker image.
- Existing Docker Compose.
- Persistent data volume.
- Health checks.
- Secure container configuration.

Preserve the production ports, reverse proxy and existing public URLs unless a verified architecture change is required.

The dashboard must work through the existing:
`https://zmovie.zeaz.dev`

Inspect the current routes before choosing an integration strategy.

Recommended dashboard routes:
- `/admin`
- `/admin/projects`
- `/admin/studio`
- `/admin/products`
- `/admin/queue`
- `/admin/workers`
- `/admin/providers`
- `/admin/media`
- `/admin/qc`
- `/admin/publishing`
- `/admin/zeazverse`
- `/admin/kids`
- `/admin/cinema`
- `/admin/analytics`
- `/admin/system`
- `/admin/audit`
- `/admin/settings`

Preserve:
- `/studio`
- `/product`
- `/membership`
- `/terms`
- `/privacy`
- Existing API routes.

Validate reverse proxy behavior, cookie security and authenticated media playback.

---

# 17. IMPLEMENTATION WORKFLOW

Use dependency-ordered vertical slices.

Stage 1: Repository audit and requirements traceability.

Stage 2: AdminLTE reference review and design tokens.

Stage 3: Shared application shell and navigation.

Stage 4: Authentication and authorization.

Stage 5: Executive dashboard.

Stage 6: Project and Production Studio integration.

Stage 7: Product Video Studio.

Stage 8: Queue and Worker Operations.

Stage 9: AI Provider Operations.

Stage 10: Media and QC.

Stage 11: Timeline and exports.

Stage 12: Publishing Center.

Stage 13: ZEAZVERSE and Kids Content Factory.

Stage 14: Cinema, commerce and membership.

Stage 15: Analytics, health and audit.

Stage 16: Real-time updates.

Stage 17: Responsive and accessibility review.

Stage 18: Security audit.

Stage 19: Automated testing.

Stage 20: Deployment validation and documentation.

Each vertical slice must be usable end to end.

Do not implement every route as an empty page.

When a capability is missing, show an honest unsupported/unavailable state and document the dependency.

Do not invent backend APIs to make the interface look functional.

---

# 18. MULTI-AGENT EXECUTION

Use specialized agents for independent workstreams.

Suggested roles:

1. Architecture and Repository Audit.
2. AdminLTE Design System.
3. Dashboard Shell and Navigation.
4. Production Studio Integration.
5. Project and Product Studio.
6. Queue and Worker Operations.
7. Media and QC.
8. Publishing and Approval.
9. ZEAZVERSE and Kids Factory.
10. API and Authentication.
11. Security Review.
12. Testing and Browser QA.
13. Deployment and Operations.
14. Independent Code Review.

Each agent must have explicit file ownership and acceptance criteria.

Avoid concurrent modification of shared files.

Establish shared route and component contracts before parallel implementation.

Use available model/provider fallbacks for implementation work where needed.

Never treat automated agent agreement as independent security approval.

---

# 19. REQUIRED DOCUMENTATION

Create or update:

- `docs/admin-dashboard/INDEX.md`
- `docs/admin-dashboard/REQUIREMENTS.md`
- `docs/admin-dashboard/ARCHITECTURE.md`
- `docs/admin-dashboard/DESIGN-SYSTEM.md`
- `docs/admin-dashboard/ROUTES.md`
- `docs/admin-dashboard/API-MAPPING.md`
- `docs/admin-dashboard/COMPONENTS.md`
- `docs/admin-dashboard/SECURITY.md`
- `docs/admin-dashboard/TEST-PLAN.md`
- `docs/admin-dashboard/DEPLOYMENT.md`
- `docs/admin-dashboard/IMPLEMENTATION-REPORT.md`

Update `docs/INDEX.md` and the production feature matrix.

Documentation must distinguish:
- Implemented.
- Tested.
- CI verified.
- Runtime verified.
- Production verified.
- Pending external validation.

---

# 20. DEFINITION OF DONE

The implementation is complete only when:

- Dashboard layout is implemented.
- Sidebar and navigation work.
- All implemented pages are functional.
- Existing Studio and Product Studio are integrated.
- Existing backend remains authoritative.
- Real data is displayed with accurate status.
- Queue and worker monitoring work.
- Media previews are secure.
- QC evidence is displayed accurately.
- Publication approval is safe.
- Kids content safety is preserved.
- Commerce and privacy boundaries are preserved.
- Authentication is enforced.
- Permissions are tested.
- Responsive views work.
- Accessibility is reviewed.
- Security tests pass.
- Existing tests pass.
- Frontend tests pass.
- Docker configuration is valid.
- Native deployment compatibility is preserved.
- Documentation is complete.
- Outstanding blockers are accurately reported.

Do not claim 100% production readiness based on static source inspection or mocked tests.

External publication, production GPU execution, model weights, live provider credentials, production-host reboot tests and independent approvals must be reported separately.

---

# 21. FINAL IMPLEMENTATION REPORT

Provide:

1. Executive summary.
2. Initial repository state.
3. Architecture decisions.
4. AdminLTE reference adaptation.
5. Implemented routes.
6. Implemented components.
7. Backend integration.
8. Real-time implementation.
9. Media and rendering features.
10. Publishing safeguards.
11. Security improvements.
12. Test execution results.
13. Build and deployment results.
14. Browser QA.
15. Accessibility results.
16. Performance measurements.
17. Files changed.
18. Remaining defects.
19. External dependencies.
20. Commit SHAs.
21. Pull request URL.
22. Rollback procedure.

Execute the complete implementation independently.

Make engineering decisions based on the existing code and contracts.

Do not stop after the design or audit phase.

Deliver working, tested, documented code with evidence for every completion claim.