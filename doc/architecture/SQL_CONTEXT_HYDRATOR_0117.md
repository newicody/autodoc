# 0117 — SQLContextHydrator

0117 adds the read-side hydration boundary above the 0116 SQL store.

SQLContextHydrator converts sql:* refs into lightweight hydrated context fragments. SQLContextStore is durable context authority.

The local installation target remains explicit:

```text
active PostgreSQL lives on fast_pool
PostgreSQL data_directory = /srv/autodoc/postgres/data
data_pool receives ZFS snapshots and backups
Qdrant 1.18.2 lives on /srv/autodoc/qdrant as projection only
OpenVINO 2026.2.1 is available in the Python AI environment with CPU and GPU devices
```

No PostgreSQL/Qdrant/OpenVINO/LLM runtime import in SQLContextHydrator.

## Boundary

`src/context/sql_context_hydrator.py` provides:

- `SqlContextHydrationRequest`: immutable list of `sql:*` refs to hydrate;
- `SqlContextHydrationPolicy`: deterministic bounds for record count, child fan-out and body size;
- `HydratedSqlContextFragment`: small fragment derived from SQL authority;
- `SqlHydratedContextBundle`: serializable bundle for later context reducers/specialists;
- `SQLContextHydrator`: read-only adapter over an injected `SQLContextStore`-like object.

The hydrator does not open a database itself. It consumes the 0116 store interface and returns bounded fragments.

## Authority vs projection

Qdrant is vector projection and retrieval, not context authority. OpenVINO produces local embeddings behind an adapter. LLM/specialist code consumes hydrated fragments later; it does not own the durable context source.

The intended path is now:

```text
Context refs / objective / artifact
-> SQLContextStore
-> SQLContextHydrator
-> HydratedSqlContextFragment[]
-> ContextReducer / InferenceContextDraft
-> OpenVINO adapter can embed hydrated text
-> Qdrant projection can store/search vectors by sql_id
-> SQLContextHydrator re-hydrates recalled sql:* refs
-> specialist / LLM boundary
```

Scheduler orchestrates context exploration jobs; it does not build variants itself.

## MVTC

MVTC remains future, not runtime in 0117. 0117 only produces deterministic hydrated fragments that future exploration machinery can consume.
