# ZeaZ Cinema Ticketing API (sandbox, synthetic data)

Separate commerce domain — not an extension of WordPress favorites/user meta.

## Run (local, sandbox only)

```bash
CINEMA_ADMIN_TOKEN=dev-admin-token python3 services/cinema-api/app.py
# health
curl -s http://127.0.0.1:8095/health
```

Seed synthetic cinemas (2 branches, halls, seat maps, 2 showtimes):

```bash
curl -s -X POST http://127.0.0.1:8095/admin/seed -H 'X-Cinema-Admin-Token: dev-admin-token'
```

## Guarantees

- `ticket_reservations UNIQUE(showtime_id, seat_no)` — double-selling
  rejected by the database, covered by concurrent tests.
- Holds expire (`release_expired_holds`), safe retries via idempotency
  keys, signed QR tickets (HMAC), check-in dedup, cancel/refund states,
  audit log (`ticket_audit`).

## PostgreSQL path

Local/test backend is SQLite (`ZMOVIE_DB_PATH`). Schema is
PostgreSQL-compatible by design: port by swapping the connection layer
to `psycopg` with `BEGIN ... ISOLATION LEVEL SERIALIZABLE` and
`ON CONFLICT DO NOTHING` (already used). Required before live sales,
with real payment/refund/legal acceptance — never enable live sales
from this sandbox alone.
