# 0113 Operational plan — context variability first

## Locked direction

The active plan is now context variability first:

```text
ContextRequest -> ContextCollector -> ContextVariant[] -> ContextReducer -> GlobalContextSnapshot -> InferenceContext -> specialist / LLM / MVTC -> solution candidate / feedback
```

The scheduler remains simple. It orchestrates context variation jobs, priorities and replayable execution. It does not contain SQL, Qdrant, OpenVINO, LLM or context-selection logic.

## What changes from the previous local-runtime roadmap

The local route runtime work remains valid as a secondary data plane. It is not the backbone of the knowledge architecture. SQL/Qdrant/OpenVINO/LLM must serve context construction and variation, not the route journal alone.

## New implementation order

### 0114 — ContextVariant contract

Add the minimal immutable contract for context requests, variants, variant sources, reducer inputs and inference context references. This must be small and versioned if public fields change.

### 0115 — SQLContextStore minimal

Implement durable structured storage for facts, documents, artifacts, route facts and context variants. SQLite can be used as a stdlib local backend while keeping the design compatible with a future PostgreSQL adapter.

### 0116 — ContextCollector / ContextReducer real path

Add a living path that creates several bounded variants and reduces them into an `InferenceContext`.

### 0117 — OpenVINO embedding worker

Add a boundary where OpenVINO can embed context material. OpenVINO remains behind an adapter and does not enter Scheduler, Dispatcher, PolicyEngine or contracts.

### 0118 — Qdrant projection and retrieval

Project embeddings into Qdrant with payloads pointing back to SQL IDs. Retrieval returns identifiers to hydrate from SQL/ContextGate.

### 0119 — LLM specialist adapter

Feed an `InferenceContext` to a specialist/LLM adapter. The output is an artifact/candidate/feedback item, not an automatic truth or direct command.

### 0120 — MVTC variation/comparison loop

Implement comparison of solution candidates and context variants under bounded search budgets.

### 0121 — Passive VisPy/Event Viewer

Render the context graph and EventBus facts passively. The viewer reads existing observation surfaces and never creates a bus.

## Explicit non-goals

```text
No CapabilityRequest security-first direction.
No ControlProxyRouteCoordinator scheduler-like direction.
No NetworkBridge/HardwareBridge active direction.
No second bus.
No route-journal-first AI pipeline.
```

## Guardrails

```text
Policy/security/zone are guardrails, not the objective.
Qdrant = vector projection and retrieval, not context authority.
OpenVINO = local embedding/inference worker behind an adapter.
LLM = specialist/enricher that consumes InferenceContext.
SQLContextStore = durable context authority.
ContextGate / TaskContext = authority for context selection.
Route mmap/eventfd = data plane, not EventBus.
EventBus = observation only.
```
