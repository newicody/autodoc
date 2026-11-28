# 0113 — Context variability relock

## Decision

0113 recenters the active architecture on context variability. The goal is not to extend a security/capability envelope. The goal is to produce solutions quickly by building several bounded context variants, comparing them, reducing them, and sending a traceable `InferenceContext` to specialists and LLM adapters.

The operating sentence is:

```text
ContextRequest -> ContextCollector -> ContextVariant[] -> ContextReducer -> GlobalContextSnapshot -> InferenceContext -> specialist / LLM / MVTC -> solution candidate / feedback
```

This phase is a relock. It adds no runtime capability and no new backend.

## Roles

```text
SQLContextStore = durable context authority
ContextGate / TaskContext = authority for context selection
Qdrant = vector projection and retrieval, not context authority
OpenVINO = local embedding/inference worker behind an adapter
LLM = specialist/enricher that consumes InferenceContext
Scheduler = orchestrates context variation jobs
PolicyEngine = minimal admission guardrail
PriorityQueue = deterministic execution order
Dispatcher = EventType -> Handler only
EventBus = observation only
ControlProxy / RouteRuntimeManager = secondary data plane for heavy payloads
Route mmap/eventfd = data plane, not EventBus
```

## Why this replaces the rejected direction

The rejected direction was to add a generic `CapabilityRequest` envelope centered on capability/security semantics. That is too far from the project objective. The scheduler must be able to orchestrate work involving SQL, Qdrant, OpenVINO and LLM adapters, but the first-class concept for this project is context variation, not capability admission.

The architecture keeps security, policy and zone filtering as guardrails, not the objective. Policy/security/zone are guardrails, not the objective.

## Scheduler view

The scheduler should see small, typed jobs such as:

```text
collect context variant
embed context chunks
project context vectors
retrieve candidates
reduce context variants
ask specialist with InferenceContext
compare solution candidates
record feedback
```

It should not directly call SQL, Qdrant, OpenVINO or an LLM runtime. Those are handlers/workers/adapters behind the kernel path.

## Context variability model

A `ContextRequest` may produce several `ContextVariant` objects:

```text
variant:minimal-fast
variant:rules-only
variant:code-current
variant:architecture-history
variant:runtime-observation
variant:github-artifacts-later
```

Each variant has a bounded purpose. Some variants may use Qdrant retrieval, some may use SQL filters only, and some may use recent runtime facts. The reducer compares the variants and builds one `InferenceContext` suitable for the specialist.

## Data authority and projections

SQL is the durable authority for structured context and stable identifiers. Qdrant stores vectors and light payloads that point back to SQL identifiers. OpenVINO produces local embeddings or small local inference results for context material. LLM adapters consume the final `InferenceContext` and produce suggestions, candidate solutions, explanations, artifacts or feedback. None of these systems bypasses the scheduler path when an action is requested.

## ControlProxy placement

ControlProxy and RouteRuntimeManager remain useful, but they are not the center of the knowledge architecture. They provide local data-plane mechanics for heavy payloads and route lifecycle. They do not create a second scheduler, they do not create a second bus, and they do not own context authority.

## Next implementation order

```text
0114 ContextVariant contract
0115 SQLContextStore minimal for facts/docs/artifacts/context variants
0116 ContextCollector / ContextReducer real path
0117 OpenVINO embedding worker for context material
0118 Qdrant projection and retrieval for context variants
0119 LLM specialist adapter over InferenceContext
0120 MVTC variation/comparison loop
0121 passive VisPy/Event Viewer of context graph and EventBus facts
```

## Boundaries

0113 does not add CLI, daemon, OpenRC service, watcher, socket, device access, Qdrant client, OpenVINO import, LLM import or SQLite runtime code. It does not modify `Scheduler.run()`, `Dispatcher`, `PriorityQueue`, `PolicyEngine`, `EventBus`, `Component.tick/yield/reply`, ControlProxy runtime code or RouteRuntimeManager.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: code_rule.md already states that GlobalContextSnapshot is transformed into InferenceContext and that Qdrant/OpenVINO/LLM backends must stay behind explicit adapters.
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
