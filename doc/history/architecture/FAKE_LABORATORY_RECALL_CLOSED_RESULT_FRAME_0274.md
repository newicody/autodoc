# Fake laboratory recall and closed ResultFrame — 0274-r4

## Purpose

0274-r4 verifies the durable laboratory `specialist_output` through the
existing recall and passive-observation path:

```text
converged r3 local handoff
-> 0261 query embedding
-> r9 query-profile compatibility
-> 0263 Qdrant reference-only recall
-> SQL rehydration
-> exact specialist_output verification
-> reused 0264 closed ResultFrame
-> reused 0265 EventBus facts
-> reused 0266 PassiveSupervisor
-> existing Cell Lens / VisPy read models
```

There is **one existing Scheduler** upstream. r4 receives its already-completed
result and creates no Scheduler or laboratory orchestrator.

## Query and passage spaces

The r3 projection uses a **passage embedding**. r4 creates a separate **query
embedding**. The roles remain distinct:

```text
passage profile role = passage
query profile role   = query
```

All other vector-space identity fields must match: backend, model, revision,
tokenizer, pooling, normalization, dimension, distance, prefix policy,
tokenization policy, collection and model digest.

The query embedding is validated before 0263 can call Qdrant.

## Recall authority

Qdrant remains reference-only recall. It returns `sql_ref` values and never
becomes the source of specialist content.

SQL remains durable authority. r4 accepts the recall only when:

- the r3 `sql_ref` is in the recall refs;
- no recalled reference is missing for the closed result;
- SQL returns a `specialist_output`;
- the rehydrated record is exactly the immutable r3 SQL record.

R4 performs no SQL write and no Qdrant write.

## Closed ResultFrame

The existing 0264 composer is reused with:

- r3 SQL write report;
- r3 passage embedding;
- r3 Qdrant projection;
- r4 recall and SQL-rehydration report.

A laboratory wrapper adds the query embedding/profile provenance without
changing the meaning of the 0264 passage/projection proof.

## Passive observation and visualization

The existing 0265 builder produces fact-only events. Publishing is optional and
uses an injected existing EventBus. EventBus remains observation-only.

The existing 0266 PassiveSupervisor consumes the report without commanding the
runtime. The visual snapshot exposes laboratory, SQL authority, Qdrant recall,
rehydration and final-artifact cells. VisPy remains passive and is not imported
by r4.

## GitHub boundary

The r3 preview is preserved unchanged behind the existing publication gate:

```text
publication_gate_required = true
remote_mutation_allowed = false
github_mutation_performed = false
```

## Next phase

**0274-r5** will compose a single operator smoke from durable SourceCandidate to
r4 closed laboratory ResultFrame and publication preview. It will remain local,
use the same Scheduler, and perform no GitHub mutation.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: missipy.laboratory.v1
context_contract_changed: false
external_dependencies_added: false
scheduler_created: false
scheduler_modified: false
parallel_orchestrator_created: false
parallel_eventbus_created: false
parallel_registry_created: false
sql_write_performed: false
qdrant_write_performed: false
qdrant_recall_refs_only: true
sql_rehydrate_performed: true
eventbus_observation_only: true
github_mutation_performed: false
network_added: false
```
