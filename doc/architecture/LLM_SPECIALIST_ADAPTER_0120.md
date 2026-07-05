# 0120 — LLM specialist adapter boundary

LLMSpecialistAdapter consumes InferenceContextDraft and hydrated SQL fragments, then delegates solution generation to an injected specialist executor.

```text
SQLContextStore
-> SQLContextHydrator
-> Hydrated SQL fragments
-> InferenceContextDraft
-> LLMSpecialistAdapter
-> injected LLM executor
-> Solution candidates carrying evidence_refs
-> GitHub project result later
```

LLM is specialist producer, not context authority. SQLContextStore is durable context authority. Qdrant is vector projection and retrieval, not context authority. OpenVINO produces embeddings behind an adapter, not prompt authority.

The adapter does not call a model directly. It builds a bounded prompt packet from refs and hydrated fragments, then validates the candidate result returned by an injected executor. Candidates carry `evidence_refs` and optional `action_refs`; they do not embed heavy payloads or replace SQL hydration.

No LLM SDK/HTTP/socket/Qdrant/OpenVINO/PostgreSQL runtime import in LLMSpecialistAdapter.

Scheduler orchestrates context exploration jobs; it does not build variants itself.

MVTC remains future, not runtime in 0120.

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

## Candidate rule

A solution candidate must be traceable:

```text
candidate_ref: specialist:solution:...
evidence_refs: sql:* / qdrant:* / ctx:* / ctx-fragment:*
action_refs: specialist:* / github:* / artifact:* / ctx-result:*
```

A candidate is not authoritative context. Review, persistence, publication, and feedback are later steps.

## Rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0120 adds a specialist adapter boundary with injected execution and introduces no kernel dependency.
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: true
```
