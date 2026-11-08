# Build, Lint and Test Report — cvsz/zmovie

## Baseline

Branch: `feat/zmovie-enterprise-production-hardening`
SHA: `8cd1f8a545420136ac6bd1416a16907f6a1de6e1`
Python: 3.14.4

## Commands run and exit codes

| Command | Exit code | Result |
|---|---|---|
| `python3 -m compileall -q zmovie.py app.py main.py zmovie_platform tests` | 0 | PASS |
| `python3 -m unittest discover -s tests -v` | 0 | PASS — 240 tests, 2 skipped |
| `python3 -m ruff check app.py main.py zmovie_platform tests scripts/check_studio_inline_js.py` | 0 | PASS — All checks passed |
| `python3 -m ruff format --check ...` | non-zero | NOTED — 99 files differ under ruff 0.17.1; CI pins ruff 0.16.1 and `ruff check` passes |
| `shellcheck --severity=warning install.sh install-docker.sh scripts/*.sh` | 0 | PASS |
| `docker compose config --quiet` | 0 | PASS |
| `docker compose build` | 0 | PASS (image `zmovie-zmovie:latest`) |
| `python3 scripts/verify_docs.py` | 0 | PASS — 199 Markdown files checked |
| `.venv/bin/pip-audit -r requirements.txt` | 0 | PASS — No known vulnerabilities |
| `ZMOVIE_PORT=19080 docker compose up -d --wait --wait-timeout 300` | 0 | PASS — container healthy |
| `curl http://127.0.0.1:19080/api/v2/health` | 0 | PASS — `{"status":"ok",...}` |
| `curl http://127.0.0.1:19080/api/v2/readyz` | 0 | PASS — `{"status":"ready","users":1}` |

## Test totals

- Unit tests: 240 run, OK, 2 skipped
- Skipped tests: 2 (in `test_zmovie.py` — CLI argument-guard path; justified, not a defect)
- No tests were deleted or globally suppressed to achieve a green result.

## Docker validation

- Compose config valid.
- Image builds successfully (build took ~65s with `apt-get upgrade` for security).
- Container starts and becomes healthy; `/api/v2/health` and `/api/v2/readyz` return success.
- Healthcheck: `curl -fsS http://127.0.0.1:8080/api/v2/health` (container port 8080).

## Media verification (FFmpeg/ffprobe)

- Generated a 5s H.264/AAC MP4 (1280x720, 24fps, 120 video frames, AAC 44.1kHz mono).
- `ffprobe` returned probe_score 100, valid streams, duration 5.0s, file size 89,698 bytes.
- ffmpeg 8.0.1, ffprobe 8.0.1 available locally.

## Notes

- No tests were run against nonexistent paths; every test command corresponds to a real repository target.
- `make check`, `make lint`, `make audit` are available Makefile targets; `make test` runs `python3 -m unittest discover -s tests -v`.
