# Multi-user migration path

See the [documentation index](../docs/INDEX.md) for canonical guides and
cross-component procedures.

The local auth/owner fields create a migration path to multi-user deployments. SQLite remains the zero-cost default; external database and object-store adapters can be added without changing the domain model.
