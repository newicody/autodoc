# ControlProxy operational plan — 0116 update

0116 does not extend ControlProxy and does not add a route-runtime service.

The operational axis is now the context data substrate:

```text
SQLContextStore = durable authority
Qdrant = projection
OpenVINO = embedding adapter
LLM = specialist boundary
RouteRuntimeManager = data-plane infrastructure only
EventBus = observation only
```

Local machine status captured for the next steps:

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

Next patches should hydrate context from SQL first, then add OpenVINO and Qdrant adapters behind explicit specialist boundaries.
