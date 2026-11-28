# ControlProxy operational plan — 0117 update

0117 does not extend ControlProxy and does not add a route-runtime service.

The operational axis is now the SQL context read path:

```text
SQLContextStore = durable authority
SQLContextHydrator = bounded read-side hydration by sql:* refs
Qdrant = projection
OpenVINO = embedding adapter
LLM = specialist boundary
RouteRuntimeManager = data-plane infrastructure only
EventBus = observation only
```

Local machine status preserved:

```text
PostgreSQL 18 service: postgresql-18
PostgreSQL data_directory: /srv/autodoc/postgres/data
PostgreSQL active storage: fast_pool
Backups/snapshots: data_pool
Qdrant binary: /usr/local/bin/qdrant
Qdrant storage: /srv/autodoc/qdrant/storage
Qdrant logs: /var/log/qdrant.log and /var/log/qdrant.err owned qdrant:logs
OpenVINO: 2026.2.1, CPU and GPU visible
```

Next patches should reduce hydrated SQL fragments into context drafts, then add OpenVINO and Qdrant adapters behind explicit specialist boundaries.
