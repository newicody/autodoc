# 0118 — OpenVINO embedding adapter boundary

OpenVINOEmbeddingAdapter builds bounded embedding requests from hydrated SQL fragments.

This phase adds the first embedding boundary after SQL hydration:

```text
SQLContextStore
-> SQLContextHydrator
-> Hydrated SQL fragments
-> OpenVINOEmbeddingAdapter
-> Embedding vectors
-> Qdrant projection adapter later
```

SQLContextStore is durable context authority. SQLContextHydrator converts sql:* refs into lightweight hydrated context fragments. OpenVINO is a specialist embedding backend behind src/inference/openvino_runtime.py. Qdrant is vector projection and retrieval, not context authority.

The adapter does not load a model itself. It receives an injected executor and an explicit `OpenVINOEmbeddingRuntimeTarget`. The documented local target is `/home/eric/model/openvino/multilingual-e5-small`, with expected dimension `384`, matching the current local E5 export.

Scheduler orchestrates context exploration jobs; it does not build variants itself. No Qdrant/PostgreSQL/LLM runtime import in OpenVINOEmbeddingAdapter. No OpenVINO package import is introduced in this adapter; the real runtime import remains isolated in `src/inference/openvino_runtime.py`, which is already the explicit OpenVINO boundary.

MVTC remains future, not runtime in 0118.

## Local installation status

The operator environment for this phase is:

```text
PostgreSQL 18 data_directory = /srv/autodoc/postgres/data
active PostgreSQL lives on fast_pool
data_pool receives ZFS snapshots and backups
Qdrant 1.18.2 lives on /srv/autodoc/qdrant
Qdrant logs are qdrant:logs
OpenVINO 2026.2.1 sees CPU and GPU
```

## Rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0118 confines embedding preparation to an explicit inference adapter boundary and introduces no new kernel dependency.
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: true
```
