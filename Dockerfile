FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /build
COPY requirements.txt ./

# Install into an isolated prefix so the runtime image never receives pip
# itself. Trivy reports pip's vendored msgpack 1.1.2 (GHSA-6v7p-g79w-8964)
# and setuptools 70.3.0 (CVE-2025-47273) as fixable HIGH findings; both are
# pip-internal, not application dependencies. Dropping pip from the final
# image removes the finding instead of documenting an exception.
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt \
    && test -x /install/bin/uvicorn

# playwright is installed under the prefix, so it is only importable with an
# explicit PYTHONPATH.
RUN PYTHONPATH="$(ls -d /install/lib/python*/site-packages)" \
    python -m playwright install chromium \
    && test -d /ms-playwright

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    ZMOVIE_DB_PATH=/app/data/zmovie.db \
    ZMOVIE_MEDIA_ROOT=/app/data/media \
    ZMOVIE_EXPORT_ROOT=/app/data/exports \
    ZMOVIE_PUBLISH_ROOT=/app/data/publish \
    ZMOVIE_TTS_PROVIDER=edge \
    ZMOVIE_TTS_VOICE=th-TH-PremwadeeNeural \
    ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK=false \
    ZMOVIE_BILIBILI_STATE_PATH=/app/data/bilibili/storage_state.json \
    ZMOVIE_AUTH_ENABLED=true

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl ca-certificates espeak-ng \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY --from=builder /ms-playwright /ms-playwright

WORKDIR /app
COPY . .

# Chromium shared libraries are required at runtime; install them with the
# Playwright CLI that was copied in above.
RUN python -m playwright install-deps chromium \
    && rm -rf /var/lib/apt/lists/* \
    && chmod -R a+rX /ms-playwright

# The base image ships pip, whose vendored copies of msgpack 1.1.2
# (GHSA-6v7p-g79w-8964) and setuptools 70.3.0 (CVE-2025-47273) are reported
# as fixable HIGH findings. Nothing needs pip at runtime: the entrypoint is
# uvicorn and the healthcheck uses curl. Remove it so the finding is resolved
# rather than documented.
RUN rm -rf /usr/local/lib/python3.*/site-packages/pip \
           /usr/local/lib/python3.*/site-packages/pip-*.dist-info \
    && test ! -d /usr/local/lib/python3.14/site-packages/pip \
    && python -c "import fastapi, uvicorn, playwright, httpx; print('runtime imports ok')"

RUN useradd --system --uid 10001 --create-home --home-dir /home/zmovie zmovie \
    && mkdir -p /app/data /app/data/bilibili /app/data/publish \
    && chown -R zmovie:zmovie /app

USER zmovie
EXPOSE 8080
VOLUME ["/app/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/api/v2/health >/dev/null || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--proxy-headers"]
