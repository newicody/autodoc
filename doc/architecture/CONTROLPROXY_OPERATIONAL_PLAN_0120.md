# ControlProxy operational plan — 0120 update

0120 keeps ControlProxy and route runtime unchanged.

Operational focus moves to specialist solution generation:

```text
InferenceContextDraft
-> LLMSpecialistAdapter
-> injected specialist executor
-> solution candidates with evidence_refs
```

ControlProxy remains data-plane infrastructure. It is not the authority for context, policy, SQL state, embeddings, Qdrant projection, or specialist output.

LLMSpecialistAdapter is a specialist boundary. It does not modify Scheduler, Dispatcher, PolicyEngine, EventBus, PriorityQueue, or RouteRuntimeManager.
