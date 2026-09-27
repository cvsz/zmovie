# Runbook — Isolated PostgreSQL Integration Tests

Status: VERIFIED 2026-09-25 (4/4 pass, full suite 178/178 with PG enabled).

## 1. Why isolated

Production has no PostgreSQL and production credentials must never be
invented. These tests run against a disposable container with synthetic
data only. MySQL (`zmovie_cinema`) is untouched.

## 2. Provision (loopback only, test-only password)

  docker run -d --name zmovie-pg-p4-test --restart no \
    -p 127.0.0.1:15432:5432 \
    -e POSTGRES_PASSWORD=test-only-disposable \
    -e POSTGRES_DB=zmovie_test postgres:18-alpine

IMPORTANT: match the server major version with the host `pg_dump` /
`pg_restore` (host has PG 18 tools). A PG 16 server fails
`test_pg_dump_restore_roundtrip` with
`unrecognized configuration parameter "transaction_timeout"` —
that is a tool-version skew, not an application defect.

## 3. Run

  ZMOVIE_PG_DSN='postgresql://postgres:test-only-disposable@127.0.0.1:15432/zmovie_test' \
    .venv/bin/python -m unittest tests.test_postgres_readiness -v

Covers: migration ledger idempotency, backup/restore rollback,
6-thread concurrent seat hold (exactly one winner — no double-sell),
pg_dump/pg_restore roundtrip.

## 4. Teardown (mandatory)

  docker rm -f zmovie-pg-p4-test

Never commit a DSN. Never point ZMOVIE_PG_DSN at production.
Production migration needs a separate reviewed plan + approval.
