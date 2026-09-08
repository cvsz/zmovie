The built-in job executor is single-node and process-local. Production multi-node deployments should replace it with a durable queue adapter while keeping the existing RenderJob contract.
