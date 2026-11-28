# 0119 — Qdrant projection adapter boundary

QdrantProjectionAdapter projects embedding vectors into Qdrant-ready points.

This phase adds the projection boundary after OpenVINO embeddings:

```text
SQLContextStore
-> SQLContextHydrator
-> OpenVINOEmbeddingAdapter
-> embedding vectors
-> QdrantProjectionAdapter
-> Qdrant-ready points
-> Qdrant recall hits
-> SQLContextHydrator re-hydrates refs
-> InferenceContextDraft
```

SQLContextStore is durable context authority. Qdrant is vector projection and retrieval, not context authority. Qdrant payload carries sql_context_ref for SQL re-hydration.

The adapter does not open a Qdrant connection. It receives an injected executor. The real local Qdrant client remains a later external adapter; this module only builds deterministic point IDs, vectors, and lightweight payloads.

No qdrant-client/PostgreSQL/OpenVINO/LLM runtime import in QdrantProjectionAdapter.

Scheduler orchestrates context exploration jobs; it does not build variants itself.

MVTC remains future, not runtime in 0119.

## Local installation status

```text
PostgreSQL 18 data_directory = /srv/autodoc/postgres/data
active PostgreSQL lives on fast_pool
data_pool receives ZFS snapshots and backups
Qdrant 1.18.2 lives on /srv/autodoc/qdrant
Qdrant storage = /srv/autodoc/qdrant/storage
Qdrant snapshots = /srv/autodoc/qdrant/snapshots
Qdrant logs are qdrant:logs
OpenVINO 2026.2.1 sees CPU and GPU
```

## Payload rule

Every projected point carries:

```text
sql_context_ref
source_ref
embedding_ref
role
embedding_backend_ref
qdrant_backend_ref
```

A Qdrant hit is never treated as content. It is only a candidate reference that must be hydrated from SQL before a specialist or LLM sees it.

## Rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0119 confines vector projection to an injected Qdrant boundary and introduces no kernel dependency.
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: true
```
