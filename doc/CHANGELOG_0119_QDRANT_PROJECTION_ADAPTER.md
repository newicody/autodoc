# 0119 — Qdrant projection adapter

Added a Qdrant projection boundary after OpenVINO embeddings:

- immutable local Qdrant target and bounded projection policy;
- deterministic Qdrant-ready points carrying `sql_context_ref`;
- projection batches and injected executor protocol;
- lightweight recall-hit contracts returning SQL refs for re-hydration;
- tests and rule guardrails preventing kernel/runtime/backend drift.

No Scheduler, Queue, Dispatcher, PolicyEngine, EventBus, RouteRuntimeManager, qdrant-client, PostgreSQL, OpenVINO, or LLM runtime coupling was added.
