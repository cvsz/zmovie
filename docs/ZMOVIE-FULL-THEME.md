# ZMOVIE — UNIVERSAL SUPERIOR ENTERPRISE UI/UX, DESIGN SYSTEM & FULL-STACK REFACTOR MASTER PROMPT

**Repository:** https://github.com/cvsz/zmovie  
**Primary branch:** main  
**Design reference:** https://github.com/ColorlibHQ/AdminLTE  
**Product:** zMovie — Self-Hosted AI Video Production Platform  
**Scope:** Entire frontend, backend, dashboard, design system, themes, UI/UX, APIs, workflows, feature integration, testing, deployment and documentation.

---

# MISSION

Act as the principal software architect, senior product designer, design-system engineer, frontend architect, backend architect, UX researcher, security engineer, QA engineer, and DevOps engineer.

Your mission is to perform a complete independent assessment and implementation of the zMovie platform.

Refactor and modernize ALL user-facing and operator-facing interfaces.

Transform the application into a unified, modern, responsive, cinematic, enterprise-grade AI content production platform.

The work includes:

1. Complete visual redesign.
2. Complete theme and design-system refactor.
3. Complete UI/UX improvement.
4. Frontend architecture refactor.
5. Backend/API integration improvements.
6. Administrative dashboard reconstruction.
7. All existing feature integration.
8. Media and workflow management improvements.
9. Production operations and monitoring UI.
10. Security, accessibility and performance.
11. Comprehensive validation.
12. Documentation and deployment completion.

This is an execution assignment.

DO NOT stop after research, screenshots, architecture proposals, wireframes, or documentation.

Inspect, implement, test, integrate, and verify actual functionality.

The target is a coherent end-to-end application, not a collection of disconnected pages.

# PHASE 0 — REPOSITORY AUDIT AND GOVERNANCE

Read all governing files before implementation.

Mandatory:

- AGENTS.md
- README.md
- SECURITY.md
- CONTRIBUTING.md
- CHANGELOG.md
- SUPPORT.md
- docs/INDEX.md
- docs/ARCHITECTURE.md
- docs/API.md
- docs/CONFIGURATION.md
- docs/OPERATIONS.md
- docs/TESTING.md
- docs/RELEASE.md
- docs/I18N.md
- docs/STATUS.md
- relevant docs and agent instructions under every affected module.

Follow repository instructions.

IMPORTANT LANGUAGE CONTRACT:

- Developer documentation and explanations: Thai.
- Source code, identifiers, routes, schemas and configuration: English.
- Preserve existing English technical terminology.

Inspect the complete repository and determine:

- Actual frontend technology.
- Existing static HTML pages.
- JavaScript modules.
- CSS architecture.
- FastAPI routers.
- Pydantic schemas.
- Database models and migrations.
- Authentication.
- Authorization.
- Media-processing pipeline.
- Queue and worker lifecycle.
- Rendering provider integrations.
- Publishing providers.
- Membership and commerce.
- Kids Content Factory.
- Analytics and monitoring.
- Deployment infrastructure.
- Existing tests and quality gates.

Do not assume a feature is complete because a route, navigation item or README mentions it.

Trace each important workflow from UI → API → service → persistence → worker/provider → observable result.

Build a feature inventory and classify capabilities:

- IMPLEMENTED
- PARTIALLY_IMPLEMENTED
- EXPERIMENTAL
- BLOCKED
- NOT_IMPLEMENTED
- EXTERNAL_DEPENDENCY
- DEPRECATED

Never misrepresent feature status.

## Existing application surfaces to investigate

- `/`
- `/studio`
- `/product`
- `/membership`
- `/admin`
- legal pages
- existing static routes and mounted assets
- API v1/v2
- creator/publishing workflows
- all module-specific routes.

Preserve legacy API compatibility unless a documented migration and compatibility strategy is implemented.

## Repository documentation

Create or update:

- docs/UI-UX-TRANSFORMATION.md
- docs/DESIGN-SYSTEM.md
- docs/FRONTEND-ARCHITECTURE.md
- docs/FRONTEND-ROUTES.md
- docs/COMPONENT-INVENTORY.md
- docs/API-INTEGRATION-MATRIX.md
- docs/BACKEND-REFACTOR.md
- docs/UX-ACCESSIBILITY.md
- docs/UI-TEST-PLAN.md
- docs/UI-IMPLEMENTATION-REPORT.md

Update docs/INDEX.md.

---

# PHASE 1 — DESIGN DIRECTION AND PRODUCT IDENTITY

## 1.1 AdminLTE reference

Use:

https://github.com/ColorlibHQ/AdminLTE

Study the actual AdminLTE source, current supported version, component organization, dashboard layouts and licensing.

Use its general enterprise-admin design patterns:

- Sidebar.
- Navbar.
- Dashboard widgets.
- Cards.
- Breadcrumbs.
- Tables.
- Forms.
- Buttons.
- Dialogs.
- Tabs.
- Navigation.
- Charts.
- Responsive grids.

Do not copy the AdminLTE logo, proprietary brand identity or unrelated example content.

Respect the applicable upstream license and asset attribution requirements.

Build an original zMovie design identity.

## 1.2 Product identity

Brand:

zMovie — AI Cinematic Production Studio

Visual direction:

- Premium.
- Cinematic.
- Creative.
- Modern.
- Professional.
- Technical.
- Media-centric.
- Minimal but powerful.
- High-quality typography.
- Rich preview surfaces.
- Consistent information hierarchy.

Avoid:

- Excessive gradients.
- Excessive glassmorphism.
- Overly bright neon.
- Excessive border decorations.
- Too many cards nested inside cards.
- Unnecessary animations.
- Inconsistent icons.
- Generic SaaS template appearance.
- Decorative controls without functionality.

## 1.3 Theme architecture

Implement three user-selectable modes:

1. Dark.
2. Light.
3. System preference.

Persist user preference safely.

Support automatic system preference detection.

Prevent theme flashing during application startup.

Ensure every component supports both dark and light modes.

Establish a single source of truth for design tokens.

## 1.4 Color system

Build semantic tokens for:

- Background.
- Surface.
- Elevated surface.
- Primary.
- Secondary.
- Accent.
- Text primary.
- Text secondary.
- Muted.
- Borders.
- Focus.
- Success.
- Warning.
- Danger.
- Information.
- Disabled.
- Overlay.

Recommended direction:

Dark:
- Deep charcoal and blue-black base.
- Elevated neutral surfaces.
- Warm white text.
- Restrained violet/cyan or cinematic indigo accents.
- Clear status colors.

Light:
- Neutral white and soft grey surfaces.
- High contrast text.
- Restrained brand accents.
- Subtle dividers.

Do not hardcode theme-specific values throughout application components.

---

# PHASE 2 — DESIGN SYSTEM

Create a centralized and reusable design system.

## 2.1 Foundations

Implement:

- Color tokens.
- Typography.
- Font weights.
- Font sizes.
- Line heights.
- Spacing.
- Layout containers.
- Grid.
- Breakpoints.
- Border radii.
- Shadows.
- Elevation.
- Motion.
- Z-index.
- Icon sizing.
- Chart palette.

## 2.2 Components

Build a reusable component library.

### Navigation
- AppSidebar
- SidebarGroup
- SidebarItem
- SidebarSubmenu
- TopNavbar
- Breadcrumbs
- MobileDrawer
- UserMenu
- CommandPalette

### Buttons
- PrimaryButton
- SecondaryButton
- GhostButton
- DangerButton
- IconButton
- SplitButton
- ButtonGroup

### Feedback
- Toast
- Alert
- StatusBadge
- ProgressBar
- Spinner
- Skeleton
- EmptyState
- ErrorState
- LoadingOverlay
- ConfirmationDialog

### Data
- DataTable
- SearchField
- FilterBar
- Pagination
- SortHeader
- StatisticCard
- MetricTrend
- ChartContainer

### Forms
- TextInput
- TextArea
- NumberInput
- Select
- MultiSelect
- DatePicker
- Checkbox
- RadioGroup
- Switch
- FileUploader
- FormSection
- FormErrorSummary

### Media
- MediaCard
- MediaGrid
- MediaPlayer
- VideoPreview
- AudioPlayer
- Thumbnail
- AssetInspector
- Timeline
- SceneCard
- StoryboardCard
- RenderProgress
- ProviderBadge

### Layout
- AppShell
- PageHeader
- PageContainer
- ContentGrid
- SettingsLayout
- SplitPanel
- ResizablePanel
- EmptyPanel

All components must be consistent and documented.

Avoid redundant one-off implementations.

---

# PHASE 3 — UNIFIED APPLICATION SHELL

Build one consistent application shell across all protected product and admin experiences.

## Sidebar sections

### WORKSPACE
- Overview
- Projects
- My Workspace
- Recent Activity

### CREATE
- Main Studio
- Story Development
- Storyboard
- Scene Editor
- Timeline Editor
- AI Prompt Generator
- Product Video Studio
- Kids Content Factory

### PRODUCTION
- Render Queue
- Production Jobs
- Workers
- Render Providers
- Media Library
- Assets
- Audio
- Subtitles
- Final Cut / Assembly

### PUBLISH
- Publishing Dashboard
- Publishing Accounts
- Publishing Calendar
- Publication History
- Platform Integrations

### BUSINESS
- Product Catalog
- Product Campaigns
- Membership
- Commerce
- Subscription History

### ANALYTICS
- Dashboard Analytics
- Production Analytics
- Usage
- Costs
- Performance
- Content Quality

### ADMINISTRATION
- Admin Dashboard
- Users
- Roles and Permissions
- Audit Logs
- System Health
- Configuration
- Feature Availability
- Security

Navigation must be based on verified implemented capabilities and user permissions.

Unavailable features must be visibly marked as unavailable or planned, not presented as functional.

## Header

Implement:

- Sidebar toggle.
- Breadcrumbs.
- Global command/search.
- Quick create.
- Notification center.
- Production queue summary.
- Worker health.
- Theme selector.
- Language selector.
- Account menu.

## Main content

Implement:

- Consistent page headings.
- Description and contextual help.
- Primary actions.
- Toolbar.
- Filters.
- Responsive layout.
- Loading states.
- Error handling.
- Empty states.
- Pagination where relevant.

## Responsive behavior

Desktop:
- Persistent collapsible sidebar.
- Full dashboard layout.

Tablet:
- Compact sidebar or drawer.
- Adaptive grid.

Mobile:
- Off-canvas navigation.
- Touch-friendly controls.
- Single-column cards.
- Responsive media previews.
- No horizontal overflow.

---

# PHASE 4 — COMPLETE PRODUCT FEATURE INTEGRATION

Refactor all existing features into the unified experience.

Do not remove working business logic.

Do not replace real workflows with mock UI.

## 4.1 Main Studio

Implement or refactor:

- Project creation.
- Project list.
- Project overview.
- Creative brief.
- Script development.
- Scene planning.
- Storyboard.
- Timeline.
- Generation prompts.
- Render configuration.
- Preview.
- Final assembly.
- Production status.
- Project history.

Provide a clear guided production flow.

## 4.2 AI Prompt Studio

Support existing capabilities:

- Cinematic prompt generation.
- Deterministic generation.
- Seed management.
- Creative styles.
- Camera and lighting parameters.
- Visual direction.
- Scene constraints.
- Prompt history.
- Copy/export.
- Reproducibility.

Preserve original deterministic behavior.

Make generated prompt components editable without silently changing stored history.

## 4.3 Story Development

Integrate:

- Topic.
- Audience.
- Genre.
- Tone.
- Narrative.
- Story structure.
- Characters.
- Scenes.
- Learning or campaign objectives.
- Script generation.
- Revisions.
- Version history.

Display the distinction between AI-generated output and human-approved content.

## 4.4 Storyboard and Timeline

Implement:

- Scene sequence.
- Scene duration.
- Visual prompt.
- Camera directions.
- Character references.
- Audio cues.
- Subtitles.
- Learning objectives.
- Timeline preview.
- Scene status.
- Validation warnings.
- Versioning.

Provide a useful storyboard-to-render workflow.

## 4.5 Rendering and Production

Integrate:

- Production jobs.
- Durable queues.
- Worker status.
- Queue depth.
- Retry status.
- Render providers.
- Provider health.
- Render configuration.
- Progress events.
- Logs.
- Preview.
- Failure diagnosis.
- Final assembly.

Render states must correspond to durable backend state.

Never fabricate completion percentages.

Implement retry and cancellation only where the backend supports safe state transitions.

Make idempotency and duplicate-job prevention visible in the design and API contracts.

## 4.6 ComfyUI and External Render Providers

Implement provider management:

- Provider registry.
- Provider type.
- Provider health.
- Endpoint status.
- Available capabilities.
- Model availability.
- Queue status.
- Render history.
- Error information.
- Configuration validation.

Never expose provider passwords or API tokens.

## 4.7 Media Library

Build:

- Media asset explorer.
- Folder navigation.
- Search.
- Tags.
- Collections.
- Asset metadata.
- Thumbnails.
- Preview.
- Video playback.
- Audio playback.
- Download where authorized.
- Delete where authorized.
- Storage information.
- Usage references.
- Asset versioning where supported.

Protect media access through server-side ownership and authorization.

Do not accept arbitrary filesystem paths from browser input.

## 4.8 Product Video Studio

Integrate:

- Product information.
- Brand.
- Category.
- Audience.
- Features.
- Benefits.
- Pricing.
- CTA.
- Visual constraints.
- Creative plan.
- Storyboard.
- Product video project creation.
- Render.
- Preview.
- Export.

Preserve factual product claims and input accuracy.

Do not invent product certifications, specifications or endorsements.

## 4.9 Membership and Commerce

Integrate:

- Membership dashboard.
- Subscription status.
- Plans.
- Usage limits.
- Entitlements.
- Transactions.
- Product commerce.
- Campaigns.
- Billing information where implemented.

Use verified backend billing state.

Never treat browser-provided pricing or entitlement information as authoritative.

## 4.10 Kids Content Factory

Keep this as a dedicated product domain.

Preserve and integrate:

- Brand management.
- Character Bible.
- Episodes.
- Scripts.
- Scene generation.
- Timeline.
- Voice profiles.
- Music license validation.
- Schedules.
- Language variants.
- Captions.
- Creative bundle import/export.
- Cost estimation.
- Publishing metadata.

Keep the existing safety checks and consent requirements intact.

For children-directed experiences, preserve appropriate safety restrictions and mandatory content classification.

Never allow the UI to bypass backend safety enforcement.

## 4.11 Publishing

Integrate all implemented publishing workflows:

- Provider connections.
- Account configuration.
- Content metadata.
- Thumbnail selection.
- Captions.
- Scheduling.
- Approval.
- Submission.
- Publication state.
- Remote confirmation.
- Publication history.
- Error recovery.

Keep the states distinct:

- Draft.
- Prepared.
- Validated.
- Approved.
- Submitted.
- Published.
- Remotely confirmed.
- Failed.

A successful API submission is not proof of public publication.

External publication requires genuine provider confirmation.

Never trigger a real external publication from development preview or isolated tests.

## 4.12 Analytics and Monitoring

Implement:

- Queue depth.
- Processing rate.
- Job success/failure.
- Render duration.
- Worker utilization.
- Provider uptime.
- Storage usage.
- Production cost.
- Media throughput.
- Publication completion.
- Audio verification results.
- Resource utilization.
- Operational alerts.

Use actual measurements.

Clearly mark unavailable metrics.

Do not insert fabricated production values.

---

# PHASE 5 — ADMINLTE-INSPIRED ADMIN DASHBOARD

Build a comprehensive operator dashboard.

## Main route

`/admin`

### Overview page

KPI widgets:

- Total users.
- Active users.
- Total projects.
- Active projects.
- Production jobs.
- Queue depth.
- Running workers.
- Failed jobs.
- Render success rate.
- Media storage.
- Provider availability.
- Publication status.

Visualizations:

- Production activity.
- Render duration.
- Job outcomes.
- Provider utilization.
- Storage usage.
- Service health.
- Usage over time.

### User Management

- User directory.
- Search.
- Filters.
- User details.
- Account status.
- Role assignments.
- Entitlements.
- Activity.
- Sessions.
- Suspension where authorized.

### Roles and Permissions

- Role list.
- Permission matrix.
- User role assignments.
- Administrative changes.
- Audit history.

Authorization must remain backend-authoritative.

### Project Administration

- All projects.
- Owner.
- Status.
- Creation date.
- Production state.
- Media usage.
- Error state.
- Administrative inspection.

### Queue and Worker Administration

- Queue list.
- Job status.
- Worker list.
- Worker heartbeat.
- Worker capacity.
- Processing rate.
- Retry state.
- Dead-letter handling if supported.
- Job detail.
- Error logs.

### Provider Administration

- Provider registry.
- Health.
- Endpoint reachability.
- Capabilities.
- Configuration.
- Usage.
- Last successful execution.

### Media Administration

- Storage overview.
- Asset inventory.
- Orphan detection where implemented.
- Usage references.
- Capacity.
- Retention policies.
- Access history.

### Publishing Administration

- Publication attempts.
- Approval state.
- External status.
- Error reports.
- Integration health.

### Security and Audit

- Audit log.
- Security events.
- Authentication attempts.
- Access denials.
- Role changes.
- Administrative activity.
- Session revocations.

### System Administration

- Application health.
- Database health.
- Queue health.
- Worker health.
- External providers.
- Configuration status.
- Background services.
- Deployment version.

Sensitive settings must never be displayed as plaintext secrets.

---

# PHASE 6 — FRONTEND ARCHITECTURE REFACTOR

First determine whether a framework migration is genuinely required.

Evaluate:

- Existing FastAPI-served static architecture.
- Existing HTML and JavaScript assets.
- Current browser compatibility.
- Existing dependencies.
- Existing tests.
- CSP and security-header constraints.
- Deployment and reverse-proxy behavior.

Prefer progressive modernization where suitable.

If introducing a React/TypeScript frontend, use a deliberate migration:

- Reuse FastAPI routes and service contracts.
- Preserve legacy endpoints.
- Separate frontend build from backend runtime.
- Integrate static output and routing safely.
- Maintain production deployment and authentication compatibility.

Do not create multiple competing frontend applications.

Establish:

- Shared application shell.
- Route architecture.
- API client.
- Domain modules.
- Component library.
- Theme provider.
- Localization provider.
- Error boundaries.
- Typed state.
- Form validation.
- Query lifecycle.
- Real-time subscriptions.

Use strict TypeScript if React is introduced.

Avoid large unnecessary dependencies.

Avoid duplicate implementations of the same product feature.

Separate presentation state from domain and server state.

---

# PHASE 7 — BACKEND AND API REFACTOR

Inspect existing FastAPI structure.

Preserve existing modular routers and service boundaries.

Review:

- API versioning.
- Authentication.
- Authorization.
- Pydantic validation.
- Database transactions.
- Queue integration.
- Durable job processing.
- Media access.
- Provider abstraction.
- Publication state machines.
- Audit records.
- Error contracts.
- Rate limiting.
- Observability.

Implement improvements only where supported by evidence.

## API contracts

Create an integration matrix mapping:

Frontend route → API endpoint → service → data model → authorization → tests.

For every endpoint verify:

- Input schema.
- Output schema.
- Authentication requirement.
- Permission.
- Validation.
- Error behavior.
- Rate limits.
- Idempotency.
- Persistence.
- Audit requirements.

Do not create frontend assumptions that disagree with actual server schemas.

## Background processing

Preserve the durable queue architecture.

Implement correct:

- State transitions.
- Retry rules.
- Lease ownership.
- Worker heartbeats.
- Recovery.
- Idempotency.
- Cancellation.
- Error reporting.
- Persistence.

Avoid retry storms.

Ensure worker failures cannot silently lose jobs or incorrectly mark work complete.

## Database

Preserve existing SQLite compatibility and migration history unless a deliberate database migration is justified.

Review:

- Schema consistency.
- Transactions.
- Indexing.
- Foreign keys.
- Data lifecycle.
- Backup.
- Restore.
- Concurrency.
- Migration rollback.
- Data integrity.

Never delete existing user projects or media during the visual refactor.

---

# PHASE 8 — API CLIENT AND REAL-TIME UX

Implement a centralized typed API client.

Requirements:

- Base URL configuration.
- Authentication handling.
- Request correlation.
- Timeouts.
- Request cancellation.
- Structured errors.
- Schema-safe response handling.
- Bounded retry for safe GET requests.
- Server-side authorization.
- No browser secrets.

Implement server-supported WebSocket or SSE events where they exist.

If no transport exists, choose bounded polling for appropriate resources.

Real-time features:

- Queue progress.
- Worker heartbeat.
- Job transitions.
- Render updates.
- Alerts.
- Provider status.
- Publication transitions.

Handle:

- Reconnection.
- Duplicate events.
- Event order.
- Stale data.
- Offline behavior.
- Cleanup on route changes.

Never invent live events.

---

# PHASE 9 — FORMS AND USER INTERACTIONS

All forms must be real, validated and connected to actual business workflows.

Implement:

- Project creation.
- Creative brief.
- Story generation.
- Storyboard editing.
- Scene configuration.
- Render configuration.
- Product planning.
- Provider configuration.
- Media metadata.
- Publishing metadata.
- Scheduling.
- Membership preferences.
- User management.
- Role management.
- Settings.

Every form must include:

- Correct types.
- Field validation.
- Server validation.
- Error handling.
- Loading states.
- Success states.
- Disabled state.
- Accessible labels.
- Confirmation for destructive actions.
- Cancellation.

Never show an artificial success message before server confirmation.

No decorative buttons.

No forms that silently discard edits.

Protect unsaved work with clear warnings where appropriate.

---

# PHASE 10 — ACCESSIBILITY AND LOCALIZATION

Target WCAG 2.2 AA.

Implement:

- Keyboard navigation.
- Screen-reader labels.
- Focus management.
- Accessible modals.
- Contrast.
- Form semantics.
- Reduced motion.
- Media controls.
- Accessible status reporting.

Localization:

- Thai.
- English.

Use BCP 47 locale identifiers:

- th-TH
- en-US

The existing I18N documentation is the starting contract.

Do not simply translate static labels while leaving errors, forms and dynamic messages untranslated.

Ensure:

- Date formatting.
- Number formatting.
- Timezones.
- Currency.
- Text direction compatibility.
- Consistent language preference.

Keep technical identifiers and API contracts independent of display language.

---

# PHASE 11 — MEDIA UX AND PERFORMANCE

Optimize image and video workflows.

Implement:

- Responsive media thumbnails.
- Lazy loading.
- Safe preview URLs.
- Appropriate poster frames.
- Video metadata loading.
- Thumbnail fallback.
- Asset pagination.
- Large-file upload progress.
- Cancellation where supported.
- Retry where safe.
- Storage usage visibility.

Do not load every media asset into browser memory.

Do not expose internal absolute paths.

Use authenticated media delivery where required.

Respect content type and file size limits.

Use efficient playback and preview strategies.

---

# PHASE 12 — SECURITY

Review:

- Authentication.
- Authorization.
- CSRF.
- XSS.
- SSRF.
- Open redirects.
- CORS.
- CSP.
- File upload attacks.
- Path traversal.
- Arbitrary file access.
- Malformed media.
- Secret exposure.
- Session handling.
- OAuth callbacks.
- Rate limits.
- SQL injection.
- Webhook verification.
- Administrative privilege escalation.

Never expose:

- Provider credentials.
- API tokens.
- OAuth refresh tokens.
- Database paths.
- Private filesystem information.
- Internal service secrets.

Preserve least-privilege access.

For administrative actions, require explicit permission and durable audit events.

Do not weaken existing security headers to make new UI assets work.

Resolve CSP compatibility safely.

Preserve Kids Content Factory's safety and consent checks.

Preserve publication approval and explicit confirmation boundaries.

---

# PHASE 13 — OBSERVABILITY

Implement consistent frontend and backend observability.

Track:

- API request latency.
- HTTP error rates.
- Worker health.
- Queue latency.
- Job failures.
- Provider errors.
- Render duration.
- Media processing failures.
- Storage pressure.
- Authentication failures.
- Frontend runtime failures.
- Publication transitions.

Use structured logs and correlation identifiers.

Do not log tokens, secrets, full private media URLs or sensitive user content.

Provide actionable error details without disclosing internal infrastructure.

---

# PHASE 14 — VALIDATION AND AUTOMATED TESTING

Review and expand repository-native validation.

Run the documented existing commands.

Baseline checks include:

```bash
python3 -m compileall -q zmovie.py app.py main.py zmovie_platform tests
python3 -m unittest discover -s tests -v
python3 scripts/verify_docs.py
node --check static/durable-worker.js
node --check static/product.js
shellcheck --severity=warning install.sh install-docker.sh scripts/*.sh
docker compose config --quiet
docker build -t zmovie:test .
```

Also run the repository's supported pytest, JavaScript tests, frontend builds and browser tests.

Do not assume commands from older documentation still match the current implementation.

Verify scripts and package definitions before modifying the validation pipeline.

## Unit testing

Test:

- Components.
- Theme switching.
- Theme persistence.
- Navigation.
- Forms.
- Validation.
- Formatting.
- State transitions.
- API response normalization.
- Error handling.

## Integration testing

Test:

- Authentication.
- Project creation.
- Storyboard.
- Job queue.
- Worker progress.
- Render provider integration using mocks.
- Media access.
- Product Studio.
- Membership entitlements.
- Publishing approval lifecycle.
- Kids content safety rules.
- Audit logging.

## Browser E2E

Verify:

1. Application loads.
2. Sidebar works.
3. Navigation works.
4. Dark mode works.
5. Light mode works.
6. System mode works.
7. Mobile layout works.
8. Project creation works.
9. Storyboard workflow works.
10. Media Library works.
11. Video preview works.
12. Render job status works.
13. Form errors render correctly.
14. Authentication works.
15. Unauthorized access is denied.
16. Admin controls are permission-protected.
17. Thai and English locale changes work.
18. Keyboard navigation works.
19. Failed API responses are handled.
20. Empty states are correct.

Mock providers only for isolated tests.

Use separate integration and UAT evidence for actual provider execution.

No tests should publish real content or consume production credentials.

---

# PHASE 15 — DEPLOYMENT AND BACKWARD COMPATIBILITY

Preserve both existing supported deployment modes:

- Docker Compose.
- Native systemd.

Inspect the real deployment configuration before making changes.

Requirements:

- Correct application entrypoint.
- Production static assets.
- API routing.
- Reverse proxy.
- Secure headers.
- Health checks.
- Resource limits.
- Graceful shutdown.
- Environment validation.
- Correct file permissions.
- Non-root execution where practical.
- Persistent database.
- Durable queue.
- Media storage.
- Backup and restore.
- Upgrade and rollback.

Do not break:

- `/api/*`
- `/api/v2/*`
- `/studio`
- `/product`
- `/membership`
- `/admin`
- media-serving routes.
- existing API clients.
- worker startup.
- scheduled operations.

Where URL behavior must change, preserve compatibility using explicit redirects and tests.

Never deploy automatically to production as part of UI development.

---

# PHASE 16 — MULTI-AGENT IMPLEMENTATION

Use specialist agents when helpful.

Assign bounded responsibilities:

1. Architecture Agent — full audit and integration design.
2. Design System Agent — visual tokens and reusable components.
3. Frontend Agent — app shell, pages and interactions.
4. Backend Agent — FastAPI contracts and integration.
5. Media Agent — upload, preview and media workflows.
6. Production Agent — queue and workers.
7. Publishing Agent — approval and external publishing flows.
8. Kids Factory Agent — child-content workflow and safety.
9. Security Agent — independent security inspection.
10. Testing Agent — unit, integration and E2E coverage.
11. DevOps Agent — Docker/systemd and deployment compatibility.
12. Independent Review Agent — final implementation review.

Agent rules:

- Define file ownership.
- Avoid simultaneous changes to shared files.
- Agree on API contracts before parallel integration.
- Keep shared domain logic authoritative.
- Avoid duplicate components.
- Integrate changes in dependency order.
- Require tests and evidence from each agent.
- Never treat multiple AI approvals as independent security review.

---

# PHASE 17 — KNOWN REPOSITORY ISSUE: P1

Investigate and resolve the currently reported issue:

https://github.com/cvsz/zmovie/issues/58

Reported problems on Main include:

1. Documentation validation fails due to a private machine-specific path in `docs/ZMOVIE-FULL-MASTER.md`.
2. Docker builder fails because Playwright installation cannot load `libatomic.so.1`.
3. Supply-chain diagnostic workflow invokes Trivy even when its prerequisites failed.
4. Docker build, vulnerability scanning and SBOM production do not currently establish a passing evidence chain.

Read the issue and verify the actual current branch before making changes.

Do not assume historical issue evidence still describes the current file contents.

Acceptance:

- Documentation validation passes.
- Builder dependencies are correctly installed in the builder stage.
- Docker builds.
- Trivy availability is explicitly verified.
- Security scan and SBOM generation are validated.
- Failed prerequisites remain a failure.
- Diagnostic artifacts are retained.
- All relevant tests pass on the exact candidate commit.

Do not update any external parent-repository submodule pointer until its package release gates are satisfied.

---

# PHASE 18 — EXECUTION ORDER

Execute as a dependency-aware refactor:

Stage 1 — Full repository audit and baseline.

Stage 2 — Product and UX inventory.

Stage 3 — Design tokens and themes.

Stage 4 — Unified application shell.

Stage 5 — Shared components.

Stage 6 — Frontend architecture.

Stage 7 — API client and state lifecycle.

Stage 8 — Main Studio.

Stage 9 — Project, storyboard and timeline.

Stage 10 — Media Library.

Stage 11 — Production and render monitoring.

Stage 12 — Product Video Studio.

Stage 13 — Publishing.

Stage 14 — Kids Content Factory.

Stage 15 — Membership and commerce.

Stage 16 — AdminLTE-inspired administration.

Stage 17 — Analytics and observability.

Stage 18 — Security and accessibility.

Stage 19 — Backend compatibility and deployment.

Stage 20 — Comprehensive automated validation.

Stage 21 — Independent review.

Stage 22 — Documentation, release and rollback preparation.

Implement functional vertical slices, not empty UI scaffolding.

Do not postpone every backend integration until after the pages have been designed.

---

# PHASE 19 — DEFINITION OF DONE

A feature is complete when:

- Its UI exists.
- Its design is consistent.
- Its interactions work.
- Its backend API exists.
- Its API permissions work.
- Its data is persisted where required.
- Its failure paths are handled.
- Its tests exist.
- Its logs are useful.
- Its documentation exists.
- Its responsive behavior is verified.
- Its security requirements are met.

The platform is considered refactored only when:

1. All existing product features have been inventoried.
2. Every implemented feature has a consistent navigation and user experience.
3. All major user workflows work end-to-end.
4. Administrative functionality is authorization-protected.
5. Media previews and production jobs work.
6. Dark, light and system themes work.
7. Thai and English localization are implemented consistently.
8. The interface is responsive.
9. Existing backend APIs retain compatibility.
10. Security constraints remain enforced.
11. Tests and builds pass.
12. Deployment paths remain supported.
13. Documentation and evidence are updated.

Never claim 100% completion without evidence.

External provider availability, real model weights, hardware acceleration, OAuth credentials and external publication confirmation must remain separate acceptance gates.

---

# PHASE 20 — FINAL IMPLEMENTATION REPORT

Produce:

1. Executive summary.
2. Existing architecture findings.
3. UI/UX before-and-after assessment.
4. New design system.
5. Theme implementation.
6. Frontend architecture changes.
7. Backend changes.
8. Routes and pages implemented.
9. Features completed.
10. Features blocked or deferred.
11. API contracts changed.
12. Database migrations.
13. Security improvements.
14. Accessibility findings.
15. Performance results.
16. Unit test results.
17. Integration test results.
18. Browser E2E results.
19. Docker validation.
20. systemd compatibility validation.
21. Known issue #58 resolution evidence.
22. Files changed.
23. Commit hashes.
24. PR URL.
25. Deployment and rollback instructions.

All claims must be supported by reproducible evidence.

# FINAL EXECUTION DIRECTIVE

Independently inspect, refactor, implement, integrate, validate and complete the entire zMovie platform within the existing repository architecture.

Prioritize maintainability, visual consistency, functional completeness, production safety, performance, accessibility and long-term extensibility.

Use AdminLTE as the design reference and create an original premium zMovie experience.

Do not stop at the design stage.

Do not stop at the planning stage.

Do not replace functional features with placeholders.

Do not break existing production capabilities.

Continue until every achievable implementation and validation requirement is completed, and explicitly report any external blocker that cannot be resolved within the repository.