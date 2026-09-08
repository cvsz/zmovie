FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ZMOVIE_HOST=0.0.0.0 \
    ZMOVIE_PORT=8080 \
    ZMOVIE_DATA_DIR=/app/data

WORKDIR /app

RUN useradd --system --uid 10001 --create-home --home-dir /home/zmovie zmovie

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY zmovie.py app.py ./
COPY static ./static
COPY prompts ./prompts

RUN mkdir -p /app/data && chown -R zmovie:zmovie /app
USER zmovie

EXPOSE 8080
VOLUME ["/app/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=3).read()"

CMD ["python", "app.py"]
