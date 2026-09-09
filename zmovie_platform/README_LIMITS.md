# Platform limits

See the [documentation index](../docs/INDEX.md) for canonical guides and
cross-component procedures.

The built-in job executor is single-node and process-local. Production multi-node deployments should replace it with a durable queue adapter while keeping the existing RenderJob contract.
