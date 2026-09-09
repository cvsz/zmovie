# Stopping the service

See the [documentation index](../docs/INDEX.md) for canonical guides and
cross-component procedures.

Graceful shutdown is handled by the ASGI server/systemd/container runtime; persistent render state is stored before provider calls return.
