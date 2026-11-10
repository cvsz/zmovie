# Runbook — Isolated PostgreSQL Integration Tests

Status: VERIFIED (4/4 pass, full suite 269/269 with PG enabled).

## 1. Why isolated

Production can utilize PostgreSQL via the Docker container service named `zpostgressql` (`postgres:18-alpine`). These tests run against a disposable container with synthetic data only.

## 2. Provision (Docker container name: zpostgressql)

  docker run -d --name zpostgressql --restart unless-stopped \
    -p 5432:5432 \
    -e POSTGRES_PASSWORD=zmovie-secure-password \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_DB=zmovie postgres:18-alpine

Alternatively, use Docker Compose:
  docker compose up -d zpostgressql

## 3. Run Tests

  ZMOVIE_PG_DSN='postgresql://postgres:zmovie-secure-password@127.0.0.1:5432/zmovie' \
    .venv/bin/python -m unittest tests.test_postgres_readiness -v

Covers: migration ledger idempotency, backup/restore rollback,
6-thread concurrent seat hold (exactly one winner — no double-sell),
pg_dump/pg_restore roundtrip.

## 4. Teardown

  docker rm -f zpostgressql
