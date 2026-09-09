# zMovie testing and verification

Tests prove the scope they exercise. This page distinguishes deterministic
repository checks from runtime, provider, hosted CI, and external publication
evidence.

## Isolated setup

Use a clean virtual environment for the declared dependency set:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip wheel
./.venv/bin/python -m pip install -r requirements.txt
```

If repository bytecode caches are not writable, use
`PYTHONDONTWRITEBYTECODE=1` or an isolated `PYTHONPYCACHEPREFIX` outside the
checkout. Do not add the environment, generated cache, database, media, or
browser state to Git.

## Local checks

The main Makefile checks are:

```bash
make test
make check
make lint
make audit
docker compose config --quiet
python3 scripts/verify_docs.py
git diff --check
```

`make check` compiles Python, runs the unit suite, validates shell syntax, and
checks the principal Studio JavaScript files. `make lint` uses Ruff when
installed. `make audit` uses pip-audit when installed. The documentation
verifier has no third-party dependency.

## CI gates

The GitHub workflow keeps a Python 3.11–3.14 matrix, project tests, prompt and
publisher smoke checks, shell syntax, JavaScript syntax, ComfyUI workflow
validation, project-reset safety, Docker Compose validation, production image
build, focused Ruff, pip-audit, and ShellCheck. Documentation verification is a
required repository gate and does not replace those checks.

## Test boundaries

- Unit tests cover deterministic prompts, API contracts, persistence, provider
  adapters, media validation, security boundaries, and publication state.
- A model-free ComfyUI smoke path proves queue/history/output integration, not
  real accelerated video generation.
- Mock rendering proves orchestration and media validation, not provider
  quality, throughput, or public publication.
- A passing local suite does not prove hosted CI, Cloudflare ownership,
  Bilibili account state, public URLs, or production infrastructure.

## Reporting results

Record the exact command, interpreter/environment, test count, skipped tests,
warnings, and exit code. Separate local results from hosted CI and runtime
observations. If a check is unavailable because a dependency, credential, or
operator-owned service is missing, report it as unverified rather than passing.
