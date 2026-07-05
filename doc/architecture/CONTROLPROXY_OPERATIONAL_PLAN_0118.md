# ControlProxy operational plan — 0118 update

0118 keeps ControlProxy and route runtime unchanged.

Operational focus moves one step forward in the context pipeline:

```text
sql:* refs
-> SQLContextHydrator
-> OpenVINOEmbeddingAdapter
-> embedding vectors
-> later Qdrant projection
```

ControlProxy remains data-plane infrastructure. It is not the authority for context, policy, SQL state, embeddings, or Qdrant projection.

The embedding adapter is a specialist boundary. It does not modify Scheduler, Dispatcher, PolicyEngine, EventBus, PriorityQueue, or RouteRuntimeManager.
