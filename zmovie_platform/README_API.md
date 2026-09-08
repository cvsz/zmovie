# zMovie v2 API module map

HTTP routing remains in `app.py`; production logic lives in this package so workers, tests and CLI reuse identical business logic.
