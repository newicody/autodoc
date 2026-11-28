# 0116 — SQLContextStore minimal

0116 introduces the first durable SQL context-store boundary.

SQLContextStore is durable context authority.

The local installation target is now explicit:

```text
active PostgreSQL lives on fast_pool
PostgreSQL data_directory = /srv/autodoc/postgres/data
data_pool receives ZFS snapshots and backups
Qdrant 1.18.2 lives on /srv/autodoc/qdrant as projection only
OpenVINO 2026.2.1 is available in the Python AI environment with CPU and GPU devices
```

This patch does not make Scheduler, Dispatcher, PolicyEngine, EventBus, RouteRuntimeManager, or ControlProxy import a database driver.

No PostgreSQL/Qdrant/OpenVINO/LLM runtime import in Scheduler.

## Boundary

`src/context/sql_context_store.py` provides:

- `SqlContextRecord`: immutable durable context record identified by `sql:*` refs.
- `DbApiSqlContextStore`: tiny DB-API boundary over an injected connection.
- `SQLiteSqlContextStore`: stdlib SQLite backend for tests and local dry runs.
- `PostgresSqlContextStoreTarget`: documented local production target, with driver import kept external.

The PostgreSQL production connection will be injected by a later adapter.  0116 deliberately does not import `psycopg`, does not open network sockets, and does not create a daemon.

## Authority vs projection

Qdrant is vector projection and retrieval, not context authority.

OpenVINO produces local embeddings behind an adapter.

LLM/specialist code consumes hydrated context later; it does not own the durable context source.

The durable path remains:

```text
SourceCandidate / GitHub artifact / local artifact
-> SQLContextStore
-> context refs
-> OpenVINO adapter can embed hydrated text
-> Qdrant projection can store/search vectors by sql_id
-> SQLContextStore re-hydrates recalled IDs
-> InferenceContext
-> specialist / LLM boundary
```

Scheduler orchestrates context exploration jobs; it does not build variants itself.

## ZFS layout

```text
fast_pool/autodoc/postgres  -> /srv/autodoc/postgres/data
fast_pool/autodoc/qdrant    -> /srv/autodoc/qdrant
data_pool/...               -> ZFS snapshots, dumps, archives, rollback material
```

The store records stable refs and small textual/metadata payloads.  Large blobs, model files, route buffers, and vector indexes stay outside the SQL record body and are referenced explicitly.

## Compatibility with the context plan

0116 prepares the durable substrate for the 0114-r2/0115 flow:

```text
ContextVariationObjective
-> ContextExplorationPlanner
-> SQL hydrate by sql:* refs
-> OpenVINO embed behind adapter
-> Qdrant recall by sql_id
-> SQL re-hydrate
-> specialist note
-> InferenceContextDraft
```

MVTC remains future exploration machinery, not runtime in 0116.
