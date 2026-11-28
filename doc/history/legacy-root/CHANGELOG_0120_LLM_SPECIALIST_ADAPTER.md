# 0120 — LLM specialist adapter

Added a specialist boundary after context draft reduction:

- bounded prompt packet from `InferenceContextDraft` plus hydrated SQL fragments;
- injected LLM specialist executor protocol;
- traceable solution candidates carrying `evidence_refs` and optional `action_refs`;
- result validation without importing LLM SDKs or backend clients;
- tests and rule guardrails preventing kernel/runtime/backend drift.

No Scheduler, Queue, Dispatcher, PolicyEngine, EventBus, RouteRuntimeManager, qdrant-client, PostgreSQL, OpenVINO, HTTP, socket, or LLM runtime coupling was added.
