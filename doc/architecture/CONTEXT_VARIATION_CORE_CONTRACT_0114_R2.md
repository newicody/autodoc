# 0114-r2 — Context variation core contract

This phase replaces the rejected linear 0114 contract with a context-centered
contract. The goal is not to implement MVTC now and not to remove MVTC from the
architecture. MVTC remains future, not runtime in 0114-r2.

context variability is the project center.

## Locked interpretation

The project goal is to produce useful solutions quickly by varying context,
calling targeted specialists, reducing context, and producing an inference
packet. The Scheduler is useful only if it can carry these bounded exploration
jobs without becoming the context engine itself.

```text
ContextVariationObjective
-> ContextVariationAxis[]
-> ContextExplorationPlan
-> ContextVariantCandidate[]
-> ContextTrajectory
-> ContextExplorationResult[]
-> InferenceContextDraft
-> later specialist / LLM call
```

Scheduler orchestrates context exploration jobs; it does not build variants itself.

## SQL / Qdrant / OpenVINO / LLM roles

SQLContextStore is durable context authority. It stores documents, facts,
artifacts, decisions, source candidates, route facts, GitHub artifacts, and
stable IDs.

Qdrant is vector projection and retrieval, not context authority. It returns
candidate IDs or refs; SQL hydrates real content.

OpenVINO produces local embeddings or light inference behind an adapter. It is a
worker/tool for context variation, not a dependency of the Scheduler.

LLM consumes InferenceContextDraft or InferenceContext through specialist boundary. It does not own the context and does not directly command ControlProxy,
EventBus, SQL, Qdrant, OpenVINO, GitHub, or the Scheduler.

## Why trajectories instead of a linear pipeline

A single linear pipeline was too rigid:

```text
request -> specs -> results -> reduction
```

The project needs context trajectories:

```text
baby-fork GitHub artifact
-> objective
-> axes: safety, material, fabrication, ergonomics, history
-> trajectories over SQL facts, Qdrant recall, OpenVINO embeddings, specialist notes
-> exploration results
-> inference context draft
```

Each trajectory is reference-only. Heavy payloads are represented as `sql:*`,
`ctx:*`, `artifact:*`, `github:*`, `route:*`, `doc:*`, `event:*`, or specialist
refs. The data plane remains for heavy payloads; the Scheduler sees bounded
jobs and references.

## Guardrails

- No MVTC runtime in 0114-r2.
- No Qdrant/OpenVINO/LLM/SQL runtime import.
- No new EventType.
- No Scheduler.run() modification.
- No Dispatcher / PriorityQueue / PolicyEngine / EventBus modification.
- No CLI, daemon, watcher, or service.
- No ControlProxy scheduler-like coordinator.
- Route mmap/eventfd remains data plane, not EventBus.

## Code rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: this phase adds pure context contracts only; it follows the existing rule that backends remain behind declared adapters and that the Scheduler sees commands/events/results/context, not concrete backends.
live_path_status: transition
live_path_uses_real_backend: n/a
context_contract_version: missipy.context.v1
context_contract_changed: true
search_commands_bounded: true
```
