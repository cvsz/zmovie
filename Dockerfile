FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ZMOVIE_DB_PATH=/app/data/zmovie.db \
    ZMOVIE_MEDIA_ROOT=/app/data/media \
    ZMOVIE_EXPORT_ROOT=/app/data/exports \
    ZMOVIE_AUTH_ENABLED=true

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd --system --uid 10001 --create-home --home-dir /home/zmovie zmovie \
    && mkdir -p /app/data \
    && chown -R zmovie:zmovie /app

USER zmovie
EXPOSE 8080
VOLUME ["/app/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/api/v2/health >/dev/null || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--proxy-headers"]
