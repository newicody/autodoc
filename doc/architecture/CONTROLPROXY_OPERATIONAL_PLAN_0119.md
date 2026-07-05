# ControlProxy operational plan — 0119 update

0119 keeps ControlProxy and route runtime unchanged.

Operational focus moves to vector projection:

```text
OpenVINOEmbeddingAdapter
-> QdrantProjectionAdapter
-> Qdrant-ready points carrying sql_context_ref
-> SQL re-hydration later
```

ControlProxy remains data-plane infrastructure. It is not the authority for context, policy, SQL state, embeddings, Qdrant projection, or specialist output.

The Qdrant projection adapter is a specialist/projection boundary. It does not modify Scheduler, Dispatcher, PolicyEngine, EventBus, PriorityQueue, or RouteRuntimeManager.
