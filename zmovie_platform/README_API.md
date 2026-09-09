# zMovie v2 API module map

See the [documentation index](../docs/INDEX.md) for canonical guides and
cross-component procedures.

HTTP routing remains in `app.py`; production logic lives in this package so workers, tests and CLI reuse identical business logic.
