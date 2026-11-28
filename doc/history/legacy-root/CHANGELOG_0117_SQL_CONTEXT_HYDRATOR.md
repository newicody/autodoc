# 0117 — SQLContextHydrator

Added a bounded read-side SQL hydration boundary:

- immutable hydration requests over `sql:*` refs;
- deterministic hydration policy for record count, child fan-out and body size;
- serializable hydrated fragments and bundles;
- runtime tests over the 0116 SQLite SQLContextStore;
- rule guardrails preventing kernel, runtime, Qdrant, OpenVINO, PostgreSQL driver or LLM coupling.

No Scheduler, Queue, Dispatcher, PolicyEngine, EventBus, RouteRuntimeManager, Qdrant, OpenVINO, PostgreSQL driver, or LLM runtime coupling was added.
