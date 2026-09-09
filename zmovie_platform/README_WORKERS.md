# Worker execution

See the [documentation index](../docs/INDEX.md) for canonical guides and
cross-component procedures.

The HTTP process uses a bounded local executor for non-blocking jobs; `python3 -m zmovie_platform.worker` provides a process boundary for external supervisors and future distributed queues.
