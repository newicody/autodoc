# 0116 — SQLContextStore minimal

Added a minimal SQL context-store boundary:

- immutable `SqlContextRecord` contracts identified by `sql:*` refs;
- DB-API `DbApiSqlContextStore` for injected connections;
- stdlib `SQLiteSqlContextStore` for deterministic tests;
- documented PostgreSQL target for the local Gentoo/OpenRC installation;
- tests and rule guardrails preventing kernel/runtime/backend drift.

No Scheduler, Queue, Dispatcher, PolicyEngine, EventBus, RouteRuntimeManager, Qdrant, OpenVINO, or LLM runtime coupling was added.
