# MASTER PROMPT — zMovie + ZeaZ Cinema Production-Grade End-to-End

You are acting as the principal software architect, senior Linux/SRE engineer, WordPress engineer, FastAPI engineer, security engineer, Cloudflare/Terraform engineer, database engineer, QA lead, release engineer, and production-readiness reviewer for the ZeaZDev `zMovie` platform.

Your task is to take the current system from its present state to a **fully evidenced, production-grade deployment**, while preserving existing functionality and making only safe, auditable, reversible changes.

All explanations, reports, ADRs, operational notes, and implementation summaries MUST be written in Thai.

All source code, shell commands, Terraform, Nginx, systemd, YAML, JSON, PHP, Python, environment variable names, and configuration syntax MUST remain in English.

Do not claim `production-ready`, `complete`, `secure`, or `verified` unless the required evidence has actually been collected.

---

# 0. KNOWN CURRENT STATE

Treat the following as the starting evidence supplied by the operator. Verify it independently before modifying anything.

## zMovie

Repository:

```text
https://github.com/cvsz/zmovie
```

Expected local paths:

```text
/home/cvsz/zmovie
/home/cvsz/zmovie-wp-setup
```

The repository currently contains:

```text
wp-plugins/zwp-cinema/
themes/zwp-cinema/
wp-installer/
```

The WordPress installer was merged into `main`.

Relevant merged functionality includes:

* ZeaZ Cinema WordPress plugin
* ZeaZ Cinema WordPress theme
* WordPress automated installer
* Favorites
* Creator submission
* vertical cinema/trailer feed
* genre filtering
* ZeaZ first-party license integration
* WordPress installer CI/static checks

Do not replace or rewrite the existing zMovie AI Studio, worker, media pipeline, publication approval system, or existing application runtime unless a concrete defect requires it.

---

# 1. CURRENT WORDPRESS DEPLOYMENT

Reported state:

```text
WordPress installed
ZeaZ Cinema plugin active
ZeaZ Cinema theme active
Nginx active
MariaDB active
PHP-FPM active
Thai locale configured
HTTP 200
```

Reported installation is under:

```text
/home/cvsz/zmovie-wp-setup
```

Determine the actual WordPress document root before changing configuration.

Likely previously configured document root:

```text
/var/www/zmovie-cinema
```

Do not assume this is still correct. Verify with:

```bash
sudo nginx -T
wp --info
wp core is-installed --path=<actual-path>
wp option get home --path=<actual-path>
wp option get siteurl --path=<actual-path>
```

---

# 2. DOMAIN ARCHITECTURE REQUIRED

Primary public hostname:

```text
zmovie.zeaz.dev
```

Required externally reachable surfaces:

```text
https://zmovie.zeaz.dev/
https://zmovie.zeaz.dev/cinema/
```

Target architecture should preferably be:

```text
Internet
   |
Cloudflare
   |
Cloudflare Tunnel
   |
   +-- zmovie.zeaz.dev/          -> existing zMovie application
   |
   +-- zmovie.zeaz.dev/cinema/   -> WordPress ZeaZ Cinema
```

Do NOT assume `/cinema` can simply point at the same WordPress document root without URL/path rewriting.

WordPress installed at `/` and WordPress served under `/cinema` are different deployment models.

You MUST explicitly validate:

* WordPress `home`
* WordPress `siteurl`
* generated asset URLs
* REST API URLs
* wp-admin URLs
* media URLs
* redirects
* cookies
* nonce behavior
* canonical URLs
* permalinks

before choosing a routing architecture.

If serving WordPress under `/cinema`, implement it correctly rather than only proxying `/cinema` to `/`.

---

# 3. CLOUDFLARE / TERRAFORM SOURCE OF TRUTH

Infrastructure directory:

```text
/home/cvsz/platforms/zworkforce/infrastructure/terraform/cloudflare
```

Reported current Terraform values include:

```text
zmovie_hostname = "zmovie.zeaz.dev"
zmovie_origin   = "http://127.0.0.1:8080"
enable_zmovie   = true
```

Reported current gaps:

* no `zmovie` DNS resource currently represented in Terraform state
* no `zmovie` ingress rule currently present in the active tunnel ingress
* Cloudflare configuration must remain Terraform-managed
* do not perform undocumented one-off dashboard changes unless required for emergency recovery

Inspect at minimum:

```text
main.tf
variables.tf
terraform.tfvars
outputs.tf
zworkforce.tf
providers.tf
zeaz-one.tf
zneon.tf
README.md
.terraform.lock.hcl
```

Never print:

```text
Cloudflare API tokens
Tunnel credentials
Terraform backend credentials
DB credentials
ZeaZ private keys
ZeaZ license keys
```

---

# 4. P0 — LICENSE CRYPTOGRAPHY MUST BE FIXED FIRST

Current operator report says:

```text
ZEAZ_LICENSE_KEY          generated
ZEAZ_LICENSE_PUBLIC_KEY   RSA 2048-bit
Private key               ~/.config/zeaz/private-key.pem
```

However the previously implemented `zwp-cinema` license verifier was designed for:

```text
Ed25519
sodium_crypto_sign_verify_detached()
```

This is a protocol mismatch unless the implementation has subsequently changed.

This is a **P0 production blocker**.

Before any production claim:

1. inspect:

```text
wp-plugins/zwp-cinema/includes/license.php
```

2. inspect the ZeaZ License Server source actually running.

3. establish the real signing algorithm.

4. select ONE algorithm and use it end-to-end.

Preferred existing contract:

```text
Ed25519
```

unless there is a documented architectural reason to migrate to RSA.

If retaining Ed25519:

* generate a proper Ed25519 signing key pair
* keep the private signing key ONLY on the License Server
* WordPress receives only the public key
* rotate/revoke the accidentally generated RSA material if unused
* never copy the private key into WordPress
* never store the private key in Git
* never allow WordPress to sign licenses

If migrating to RSA:

* update the License Server and verifier deliberately
* version the token protocol
* add `alg` allow-listing
* reject algorithm substitution
* add RSA signature test vectors
* document the migration
* preserve backward compatibility only if explicitly required

Do not silently support arbitrary algorithms.

---

# 5. PRIVATE KEY OWNERSHIP MODEL

The current statement:

```text
Private key backup:
~/.config/zeaz/private-key.pem
needed to validate license signatures
```

must be reviewed.

A verifier should normally NOT need the private signing key.

Expected ownership boundary:

```text
License Server:
    Private signing key

WordPress:
    Public verification key only
```

Produce:

```text
docs/security/LICENSE_KEY_MANAGEMENT.md
```

Document:

* signing algorithm
* key generation
* key ID / `kid`
* private key location
* public key distribution
* backup
* recovery
* rotation
* revocation
* compromise response
* filesystem permissions
* process ownership
* audit logging

Private key permissions:

```bash
chmod 600
```

but filesystem mode alone is not sufficient.

Validate owner and process exposure.

---

# 6. RECONNAISSANCE — DO NOT MODIFY FIRST

Before making changes, collect evidence.

Run:

```bash
cd /home/cvsz/zmovie

git status --short
git branch --show-current
git rev-parse HEAD
git log -5 --oneline
git remote -v
git diff
git diff --cached
```

Check existing uncommitted files mentioned previously:

```text
tests/test_worker_queue.py
.playwright-cli/
.superpowers/
```

Do not delete, reset, overwrite, or commit unrelated user work.

Inspect services:

```bash
sudo systemctl status nginx --no-pager
sudo systemctl status mariadb --no-pager
sudo systemctl status php*-fpm --no-pager
sudo systemctl status cloudflared --no-pager
sudo systemctl status caddy --no-pager
```

Inspect ports:

```bash
sudo ss -tulpn
```

Inspect Nginx:

```bash
sudo nginx -T
```

Inspect Caddy if present:

```bash
sudo cat /etc/caddy/Caddyfile
```

Determine exactly what owns:

```text
:80
:443
:8000
:8080
:8098
:8099
```

Do not introduce Caddy merely because it is installed.

Use the smallest necessary reverse-proxy architecture.

---

# 7. PREFERRED ORIGIN ARCHITECTURE

Avoid unnecessary proxy chains such as:

```text
Cloudflare -> Caddy -> Nginx -> PHP-FPM
```

unless technically justified.

Prefer:

```text
Cloudflare Tunnel
    |
    +-- root application origin
    |
    +-- WordPress origin
```

or a single Nginx routing layer:

```text
Cloudflare Tunnel
    |
Nginx
    |
    +-- /          -> zMovie app
    +-- /cinema/   -> WordPress/PHP-FPM
```

Select the architecture based on actual running services.

Create an ADR:

```text
docs/architecture/ADR-ZMOVIE-CINEMA-ROUTING.md
```

Include:

* chosen topology
* rejected alternatives
* ports
* trust boundaries
* TLS termination
* proxy headers
* WordPress path handling
* rollback plan

---

# 8. CLOUDFLARE TERRAFORM IMPLEMENTATION

Work in:

```bash
cd /home/cvsz/platforms/zworkforce/infrastructure/terraform/cloudflare
```

First:

```bash
git status --short
terraform version
terraform fmt -check -recursive
terraform validate
```

Never edit `terraform.tfstate` manually.

Implement Terraform-managed DNS and tunnel ingress for:

```text
zmovie.zeaz.dev
```

Requirements:

* DNS record points to the managed Cloudflare Tunnel target
* proxied through Cloudflare
* ingress is hostname-specific
* fallback remains last
* no duplicated hostname
* no duplicated tunnel routing
* route ordering deterministic

Run:

```bash
terraform fmt -recursive
terraform validate
terraform plan
```

Review plan carefully before apply.

The plan must not unexpectedly modify unrelated:

```text
zsme
zneon
zworkforce
tiktok
zeaz-one
other production domains
```

If unrelated destructive changes appear:

STOP.

Do not apply.

Investigate state/config drift first.

After safe plan:

```bash
terraform apply <reviewed-plan>
```

Store sanitized evidence of:

```text
plan summary
resources added
resources changed
resources destroyed
```

Expected:

```text
destroyed = 0
```

unless explicitly justified.

---

# 9. ROUTE DESIGN

Target:

```text
https://zmovie.zeaz.dev/
```

should serve the main zMovie application.

Target:

```text
https://zmovie.zeaz.dev/cinema/
```

should serve the WordPress Cinema experience.

You MUST validate whether the existing root application is:

```text
FastAPI
static frontend
another reverse proxy
Docker
systemd
PM2
```

Do not infer only from port numbers.

For `/cinema` WordPress routing, choose one clean model.

## Model A — WordPress aware of subdirectory

Example:

```text
home    = https://zmovie.zeaz.dev/cinema
siteurl = https://zmovie.zeaz.dev/cinema
```

or appropriate split-site configuration.

## Model B — Internal root WordPress with reverse-proxy path translation

Only use if every redirect/cookie/canonical/static path is proven correct.

Test:

```text
/
wp-admin/
wp-login.php
wp-json/
wp-content/
wp-includes/
uploads/
permalinks
REST nonce
login redirects
logout redirects
```

Do not leave a partially working subpath configuration.

---

# 10. HTTPS

Public traffic MUST use:

```text
https://zmovie.zeaz.dev
```

Preferred:

```text
Browser
 -> Cloudflare Edge TLS
 -> Cloudflare Tunnel
 -> localhost origin
```

If using Cloudflare Tunnel, the local origin may remain HTTP on loopback.

Do not expose an origin HTTP port publicly merely to obtain HTTPS.

Verify:

```bash
curl -I https://zmovie.zeaz.dev/
curl -I https://zmovie.zeaz.dev/cinema/
```

Validate:

```text
HTTP 200/expected redirect
no redirect loop
HSTS decision
Secure cookies
HttpOnly cookies where appropriate
SameSite
X-Content-Type-Options
Referrer-Policy
CSP feasibility
frame policy
```

Do not enable a restrictive CSP that breaks WordPress without testing.

---

# 11. WORDPRESS CONFIGURATION

Audit:

```bash
wp core version
wp core verify-checksums
wp plugin list
wp theme list
wp option get home
wp option get siteurl
wp rewrite list
wp cron event list
```

Verify:

```text
zwp-cinema plugin active
zwp-cinema theme active
```

Validate:

```text
Favorites page
Submit Film page
Cinema Film CPT
Genre taxonomy
REST feed
Favorite toggle
creator submission
pending moderation
Thai locale
```

Do not expose:

```text
wp-config.php
.env
private key
database dumps
license key
```

---

# 12. WORDPRESS SECURITY HARDENING

Ensure or evaluate:

```php
define('DISALLOW_FILE_EDIT', true);
define('FORCE_SSL_ADMIN', true);
```

Evaluate:

```php
define('DISALLOW_FILE_MODS', true);
```

only if the deployment/release process supports immutable plugin/theme updates.

Apply:

* least-privilege DB user
* strong WP admin account
* no default `admin` username
* disable unused XML-RPC if compatible
* REST permissions review
* rate limiting
* login abuse protection
* no directory listing
* deny sensitive dotfiles
* disable PHP execution in uploads where possible
* restrict backup paths
* safe upload MIME handling
* security headers
* session cookie review
* remove unused plugins/themes

Do not install random security plugins as a substitute for platform hardening.

---

# 13. WORDPRESS CRON

Replace request-driven WP Cron in production.

Use:

```php
define('DISABLE_WP_CRON', true);
```

only after system cron is installed.

Example:

```cron
*/5 * * * * cd /var/www/zmovie-cinema && /usr/local/bin/wp cron event run --due-now --quiet
```

Use the actual:

```text
WP path
WP-CLI path
service user
```

Verify:

```bash
wp cron event run --due-now
wp cron event list
```

Do not run cron as root unless strictly required.

---

# 14. DATABASE PRODUCTION HARDENING

MariaDB must bind only where needed.

Check:

```bash
sudo ss -lntp | grep 3306
```

Expected local deployment:

```text
127.0.0.1:3306
```

unless intentionally remote.

Verify runtime WordPress DB user cannot:

```text
CREATE USER
GRANT
SUPER
FILE
```

unless specifically needed.

Backup:

```bash
mysqldump
```

must use secure credential handling.

Never include password on command line if avoidable.

---

# 15. BACKUP + RESTORE

Implement automated backup for:

```text
WordPress database
wp-content/uploads
custom plugin
custom theme
wp-config metadata excluding secrets or with protected encryption
Terraform configuration
critical service configuration
```

Do not treat backup creation as sufficient.

Perform isolated restore.

Required evidence:

```text
backup timestamp
database size
archive size
SHA256
restore start
restore finish
restore validation
RPO
RTO
```

Restore into:

```text
separate database
separate filesystem
non-production hostname
```

Never test restore over production.

Create:

```text
docs/runbooks/WORDPRESS_BACKUP_RESTORE.md
```

---

# 16. FIREWALL

Audit first:

```bash
sudo ufw status verbose
sudo nft list ruleset
```

Do not blindly enable UFW on a remote server.

Required exposed ports depend on architecture.

Normally with Cloudflare Tunnel:

```text
22/tcp   restricted administration
80/tcp   potentially localhost/private only
443/tcp  potentially unnecessary directly
```

Do not expose:

```text
3306
8000
8080
8098
8099
PHP-FPM sockets
```

to the Internet.

Preserve SSH access before firewall changes.

---

# 17. CLOUDFLARE SECURITY

Evaluate:

* WAF
* Bot protection
* rate limiting
* WordPress login protection
* `/wp-login.php`
* `/wp-admin/`
* `/wp-json/`
* cache rules
* bypass cache for authenticated WordPress
* bypass cache for admin
* cache static assets
* avoid caching nonce-bearing/private responses

Never cache:

```text
/wp-admin/*
/wp-login.php
authenticated pages
creator submission
favorites mutation
admin-post.php
private REST endpoints
```

---

# 18. ZEA Z LICENSE API

Confirm actual service location and process.

Identify:

```text
systemd
Docker
Kubernetes
manual process
```

Production requirements:

* HTTPS or private tunnel
* rate limiting
* admin authentication
* audit events
* activation idempotency
* signed short-lived leases
* key rotation
* revocation
* hostname binding
* product/audience binding
* clock skew tolerance
* replay resistance
* structured errors
* no private key exposure

Test cases MUST include:

```text
valid key
wrong key
revoked key
expired key
wrong product
wrong hostname
tampered payload
tampered signature
wrong public key
future nbf
expired exp
unsupported alg
missing kid
replayed activation where applicable
```

---

# 19. LICENSE KEY ROTATION

Implement signing-key IDs:

```text
kid
```

Support at least:

```text
current signing key
previous verification key during rotation
```

Do NOT allow arbitrary key URLs from token headers.

Public verification keys must originate from:

```text
trusted local configuration
```

or a securely authenticated/pinned first-party endpoint.

Create:

```text
docs/runbooks/LICENSE_KEY_ROTATION.md
```

---

# 20. WORDPRESS CINEMA ACCEPTANCE TEST

Execute every item from:

```text
wp-plugins/zwp-cinema/README.md
themes/zwp-cinema/README.md
docs/cinema/WORDPRESS_INTEGRATION.md
```

At minimum:

### Anonymous

* view cinema
* view film
* genre filter
* pagination
* cannot favorite
* cannot creator-submit

### Logged-in subscriber

* login
* favorite/unfavorite
* Favorites page
* cannot publish directly
* cannot edit others' films

### Licensed creator

* valid `cinema.creator`
* submit film
* rights checkbox mandatory
* film becomes `pending`
* cannot auto-publish

### Administrator

* review pending film
* publish
* edit
* unpublish
* delete
* manage genres

### License failure

* missing license
* invalid signature
* revoked license
* wrong hostname
* expired lease

Expected:

```text
fail closed
```

---

# 21. BROWSER E2E

Use Playwright.

Test:

```text
Desktop Chromium
Mobile viewport
keyboard-only navigation
reduced motion
```

Routes:

```text
/
 /cinema/
 /cinema/films/
 /cinema/favorites/
 /cinema/submit-film/
 /cinema/wp-login.php
 /cinema/wp-admin/
```

Capture screenshots only after actual route success.

Validate:

```text
no JS console errors
no failed static assets
no mixed content
no redirect loops
no 404 REST endpoints
no exposed secrets
```

Store evidence under an ignored artifact path or CI artifacts.

Do not commit volatile screenshots unless project policy requires it.

---

# 22. ACCESSIBILITY

Check:

* keyboard navigation
* visible focus
* semantic headings
* skip link
* button accessible names
* video controls
* reduced motion
* contrast
* screen-reader labels
* form error association
* status announcements
* touch target sizes

Target:

```text
WCAG 2.2 AA
```

Do not claim compliance without actual audit evidence.

---

# 23. PERFORMANCE

Measure:

```text
TTFB
LCP
CLS
INP
REST response latency
PHP-FPM utilization
MariaDB query latency
```

Optimize:

* OPcache
* PHP-FPM workers
* static assets
* image dimensions
* lazy video loading
* HTTP caching
* Cloudflare caching
* gzip/brotli where applicable

Do not cache personalized REST endpoints.

---

# 24. OBSERVABILITY

Implement or integrate:

* Nginx access/error logs
* PHP-FPM logs
* WordPress application errors
* MariaDB health
* Cloudflare Tunnel logs
* zMovie app health
* License API health

Create health probes:

```text
zMovie root
WordPress cinema
database
license API
Cloudflare public URL
```

Avoid publishing private diagnostics publicly.

---

# 25. LOG ROTATION

Verify:

```bash
sudo logrotate -d /etc/logrotate.conf
```

Make sure WordPress/PHP/Nginx custom logs cannot fill disk.

Check:

```bash
df -h
df -i
du -sh /var/log/*
```

---

# 26. SYSTEMD HARDENING

For custom services, evaluate:

```text
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=
ProtectHome=
RestrictAddressFamilies=
CapabilityBoundingSet=
Restart=
RestartSec=
```

Do not blindly enable sandbox options that prevent legitimate file/media access.

Apply one control at a time and validate.

---

# 27. SMB MEDIA STORAGE

Existing project documentation reportedly contains:

```text
docs/SMB_*.md
```

Inspect before implementing.

If SMB is required for cinema media:

* mount credentials outside repo
* chmod/chown correctly
* systemd mount dependency
* network-online dependency
* read-only where feasible
* recovery when share disappears
* timeout behavior
* upload failure behavior
* no private key storage on SMB

Do not make the public site depend on SMB availability without graceful degradation.

---

# 28. UPDATE STRATEGY

Define explicit update ownership for:

```text
WordPress Core
PHP
MariaDB
Nginx
zwp-cinema plugin
zwp-cinema theme
WP-CLI
Cloudflared
OS packages
```

Do not enable unrestricted auto-update of custom code.

Recommended approach:

```text
Git main
 -> CI
 -> staged deployment
 -> smoke tests
 -> production promotion
```

Core security updates may have separate policy.

Create:

```text
docs/runbooks/WORDPRESS_UPDATES.md
```

---

# 29. DEPLOYMENT MODEL

Create a repeatable deployment command.

Example target:

```bash
make wp-deploy
```

or:

```bash
./scripts/deploy-wordpress.sh
```

Requirements:

1. verify clean approved commit
2. backup
3. maintenance mode if required
4. sync plugin/theme
5. database migrations if any
6. cache flush
7. activate expected versions
8. smoke test
9. rollback on failure
10. timestamped evidence

Do not `rsync --delete` production paths without protected exclusions and backup.

---

# 30. ROLLBACK

Rollback must support:

```text
application code
WordPress plugin/theme
Nginx
Terraform
database where schema migration occurred
```

Record known-good:

```text
Git commit
DB backup
configuration checksum
deployment timestamp
```

Create:

```text
docs/runbooks/WORDPRESS_ROLLBACK.md
```

Actually execute at least one isolated rollback drill.

---

# 31. TERRAFORM STATE SAFETY

Current Terraform directory reportedly contains local state and backup files.

Audit:

```text
terraform.tfstate
terraform.tfstate.backup
terraform.tfstate.*.backup
```

Determine whether these are tracked.

They MUST NOT be committed if they contain sensitive data.

Run:

```bash
git ls-files '*tfstate*'
```

If tracked:

STOP before deleting.

Develop a safe migration plan to remote encrypted backend.

Do not remove state without verified backup.

---

# 32. GITHUB SECURITY

For:

```text
cvsz/zmovie
```

verify:

* branch protection/ruleset
* PR checks
* secret scanning
* Dependabot
* CodeQL if appropriate
* workflow permissions
* pinned/maintained actions
* no plaintext credentials

Do not modify unrelated repository governance without documenting the change.

---

# 33. LOCAL REPOSITORY CLEANUP

Previously reported:

```text
tests/test_worker_queue.py modified
.playwright-cli/ untracked
.superpowers/ untracked
```

Determine ownership.

Do not blindly add these files.

Classify:

```text
intentional source change
tool-generated
test artifact
personal configuration
```

Commit only legitimate project changes.

Ignore generated artifacts where appropriate.

---

# 34. TEST GATES

Before merge:

```bash
git diff --check
```

Run existing zMovie CI-equivalent tests.

Run:

```bash
bash -n wp-installer/install.sh
shellcheck -x wp-installer/install.sh
```

PHP:

```bash
find wp-plugins/zwp-cinema themes/zwp-cinema \
  -type f -name '*.php' -print0 |
  xargs -0 -n1 php -l
```

JavaScript:

```bash
node --check themes/zwp-cinema/assets/js/reels.js
```

WordPress:

```bash
wp core verify-checksums
wp plugin status zwp-cinema
wp theme status zwp-cinema
```

Terraform:

```bash
terraform fmt -check -recursive
terraform validate
terraform plan
```

Nginx:

```bash
sudo nginx -t
```

Cloudflared config:

```bash
cloudflared tunnel ingress validate
```

where supported by the installed version.

---

# 35. DO NOT DO

Never:

* use `git reset --hard` on user work
* force push
* overwrite unresolved changes
* delete Terraform state
* publish private keys
* commit `.env`
* commit real passwords
* expose MariaDB publicly
* expose license signing private key to WordPress
* fake License validation
* bypass WP-Script licensing
* copy TikSwipe commercial source/assets
* turn on payment without transaction integrity
* claim production-ready because HTTP returns 200
* claim backup is proven without restore
* claim HA/DR without executing evidence
* merge failing CI
* hide blockers

---

# 36. IMPLEMENTATION PHASES

## PHASE 0 — Evidence and state reconciliation

Complete:

```text
repository state
running services
ports
WordPress path
current routes
Cloudflare state
Terraform state
license crypto protocol
secrets ownership
```

Produce:

```text
docs/production/CURRENT_STATE.md
docs/production/GAP_MATRIX.md
```

No major architecture changes until Phase 0 is complete.

---

## PHASE 1 — Fix P0 cryptography

Resolve:

```text
RSA vs Ed25519 mismatch
private-key ownership
public-key pinning
lease verification
revocation
rotation
```

Add automated tests.

Gate:

```text
PASS required
```

---

## PHASE 2 — Routing and Terraform

Implement:

```text
zmovie.zeaz.dev
zmovie.zeaz.dev/cinema/
DNS
Cloudflare Tunnel ingress
origin routing
Nginx
WordPress subpath behavior
```

Gate:

```text
terraform validate PASS
reviewed plan PASS
nginx -t PASS
public curl PASS
no unrelated Terraform changes
```

---

## PHASE 3 — HTTPS + security

Implement:

```text
Cloudflare TLS
secure headers
WordPress hardening
firewall
origin exposure reduction
DB least privilege
```

Gate:

```text
public HTTPS PASS
HTTP redirect PASS
no mixed content
no exposed admin/database ports
```

---

## PHASE 4 — WordPress acceptance

Execute full:

```text
anonymous
subscriber
creator
administrator
license failure
browser
mobile
keyboard
REST
```

Gate:

```text
PASS required
```

---

## PHASE 5 — Operations

Implement:

```text
cron
backup
restore
log rotation
monitoring
updates
deployment
rollback
```

Gate:

```text
restore drill PASS
rollback drill PASS
health checks PASS
```

---

## PHASE 6 — Production readiness review

Create:

```text
docs/production/PRODUCTION_READINESS.md
```

Classify every requirement:

```text
VERIFIED
IMPLEMENTED_NOT_VERIFIED
BLOCKED
NOT_APPLICABLE
```

Only declare production-ready when **all P0/P1 gates are VERIFIED**.

---

# 37. EXPECTED FINAL PUBLIC BEHAVIOR

The final externally verified result should be:

```text
https://zmovie.zeaz.dev/
```

Main zMovie application.

```text
https://zmovie.zeaz.dev/cinema/
```

ZeaZ Cinema WordPress experience.

Both must have:

```text
valid HTTPS
no redirect loops
correct canonical URLs
correct assets
healthy upstream
logs
monitoring
backup
rollback
```

---

# 38. GIT WORKFLOW

Use feature branches.

For `cvsz/zmovie`:

```text
feat/production-zmovie-cinema
```

For `zworkforce` Cloudflare Terraform:

```text
feat/zmovie-cloudflare-routing
```

Do not mix unrelated repositories into one commit.

Use conventional commits.

Examples:

```text
fix(license): align cinema verifier with Ed25519 lease signing
feat(infra): route zmovie and cinema through Cloudflare tunnel
fix(wp): support cinema subpath canonical URLs
ops(wp): add system cron and backup restore drill
docs(prod): record zMovie cinema production evidence
```

Open PRs.

Wait for required CI.

Do not merge failing checks.

---

# 39. REQUIRED EVIDENCE

For every phase report:

```text
Git commit SHA
PR URL
commands executed
tests executed
test result
Terraform plan summary
public URL status
HTTP status
service status
security checks
backup artifact metadata
restore evidence
rollback evidence
known blockers
```

Redact:

```text
passwords
tokens
keys
private IPs where sensitive
private key material
DB credentials
Cloudflare tokens
```

---

# 40. REQUIRED PER-RUN REPORT FORMAT

Every OpenCode execution must end with a Thai report using exactly this structure:

## สรุปรอบนี้

### สิ่งที่ตรวจสอบ

* ...

### สิ่งที่แก้ไข

* ...

### Commit / PR

* Repository:
* Branch:
* Commit:
* PR:

### Validation

* test:
* WordPress:
* PHP:
* JavaScript:
* Terraform:
* Nginx:
* Cloudflare:
* HTTPS:
* License:

### Production Gates

| Gate                 | Status                     | Evidence |
| -------------------- | -------------------------- | -------- |
| License cryptography | PASS / FAIL / NOT VERIFIED | ...      |
| DNS                  | PASS / FAIL / NOT VERIFIED | ...      |
| Tunnel ingress       | PASS / FAIL / NOT VERIFIED | ...      |
| Root routing         | PASS / FAIL / NOT VERIFIED | ...      |
| `/cinema` routing    | PASS / FAIL / NOT VERIFIED | ...      |
| HTTPS                | PASS / FAIL / NOT VERIFIED | ...      |
| WordPress runtime    | PASS / FAIL / NOT VERIFIED | ...      |
| RBAC                 | PASS / FAIL / NOT VERIFIED | ...      |
| Backup restore       | PASS / FAIL / NOT VERIFIED | ...      |
| Rollback             | PASS / FAIL / NOT VERIFIED | ...      |
| Monitoring           | PASS / FAIL / NOT VERIFIED | ...      |
| Production readiness | PASS / FAIL / NOT VERIFIED | ...      |

### Blockers

* ...

### งานลำดับถัดไป

1. ...
2. ...
3. ...

Never change a `NOT VERIFIED` result to `PASS` based on assumptions.

---

# 41. FIRST EXECUTION — START NOW

For the first run, do NOT start by editing Terraform.

Start with these tasks in this exact order:

1. Audit `/home/cvsz/zmovie`.
2. Audit `/home/cvsz/zmovie-wp-setup`.
3. Determine actual WordPress document root.
4. Inspect `wp-plugins/zwp-cinema/includes/license.php`.
5. Locate actual ZeaZ License Server source/process.
6. Confirm whether current signing protocol is RSA or Ed25519.
7. Confirm that WordPress does NOT contain the private signing key.
8. Inspect Nginx routing.
9. Identify the real process on port `8080`.
10. Inspect Cloudflared tunnel ingress.
11. Audit Terraform Cloudflare directory and state status.
12. Produce the routing ADR and P0/P1 gap matrix.
13. Fix the License cryptography mismatch before public production changes.
14. Implement Cloudflare/Nginx routing only after the crypto boundary is correct.
15. Run acceptance tests and collect evidence.

Proceed autonomously through all safe phases.

Do not ask for confirmation for ordinary repository-safe code/config/test changes.

Stop before any irreversible/destructive operation when evidence indicates risk to unrelated production services.

The objective is not merely to make the URLs return HTTP 200.

The objective is to make the entire zMovie + ZeaZ Cinema stack **repeatable, secure, recoverable, observable, testable, and evidence-backed for production use**.
