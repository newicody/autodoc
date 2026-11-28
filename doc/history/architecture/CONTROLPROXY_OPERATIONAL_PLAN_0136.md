# 0136 operational note — vector indexing uses existing Qdrant path

0136 does not add a Qdrant runtime client, worker, scheduler branch, or RouteProxy branch. It locks the existing projection path before the real handler is wired.

```text
Scheduler
-> VectorIndexingJobPlan
-> VectorProjectionJob
-> existing Qdrant projection adapter
-> VectorCollectionRegistry
-> Qdrant collection
-> SQL ref for durable hydration
```

RouteProxy and `/dev/shm` may later carry request/result frames, but Qdrant projection remains an inference/vector adapter responsibility, not a Scheduler or RouteProxy responsibility.
