# Fake laboratory closed local handoff — 0274-r3

## Purpose

0274-r3 closes the converged fake laboratory result through existing local
surfaces:

```text
FakeLaboratoryDeliberationResult
-> existing SQLContextStore
-> existing 0261 OpenVINO/E5 path
-> existing r9 embedding compatibility gate
-> existing 0262 Qdrant projection
-> fact-only EventBus events
-> existing PassiveSupervisor read model
-> existing visual read/layout models
-> local GitHub publication preview
```

There is **one existing Scheduler** upstream. r3 receives the completed r2
result and does not create or run a Scheduler.

## Durable authority

SQL remains durable authority.

The final `FinalArtifactEnvelope` becomes one deterministic
`specialist_output` record. Before writing, r3 checks the existing record:

- absent: insert through the existing store;
- identical: idempotent replay;
- different under the same `sql_ref`: refuse the immutable collision.

The laboratory provider does not own the store.

## Vector path

The vector path reuses:

```text
0261 SQL readback -> OpenVINO/E5 passage embedding
r9 EmbeddingSpaceProfile compatibility gate
0262 Qdrant projection carrying payload.sql_ref
```

Qdrant remains projection-only. An incompatible model, tokenizer, role,
dimension, normalization or profile blocks the write before Qdrant.

0274-r3 does not add recall. **0274-r4** will reuse the existing 0263 recall and
SQL rehydration path for the laboratory output, then close a laboratory-specific
ResultFrame.

## Observation and visualization

EventBus remains observation-only.

Four immutable facts are produced:

- deliberation completed;
- specialist output persisted;
- vector projection state;
- GitHub preview pending.

When publishing is enabled, they use the injected existing EventBus with no
Request and `command=false`.

The existing PassiveSupervisor consumes a compatible fact report. The existing
renderer-neutral visual read and layout models then display laboratory,
specialist, deliberation, synthesis, final artifact, SQL and Qdrant cells.

VisPy remains passive and is not imported by the handoff.

The visual models are extended only to understand laboratory refs/zones and the
existing read-model edge keys (`edge_id`, `edge_kind`, `target_ref`).

## GitHub boundary

The preview is local:

```text
status = pending
review_surface = context.github_publication_review
publication_gate_required = true
remote_mutation_allowed = false
github_mutation_performed = false
```

It does not replace the existing publication review or publication gate.

## Authority summary

```text
Scheduler                 existing upstream authority
SQL                       durable authority
OpenVINO/E5               embedding only
Qdrant                    projection only
EventBus                  observation only
PassiveSupervisor         passive read model
Cell Lens / VisPy         passive visualization
GitHub                    local preview only
```

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
sql_remains_authority: true
qdrant_projection_only: true
eventbus_observation_only: true
github_mutation_performed: false
network_added: false
```
