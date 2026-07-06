# 0137 — ControlProxy operational plan update

0137 does not add ControlProxy runtime behavior. It adds a readiness gate before the first local vector-indexing smoke test.

The next live path must reuse:

```text
Scheduler route handler
RouteProxyRuntime
VectorIndexingJobPlan
OpenVINO/E5 membrane
Qdrant projection adapter
SQLContextStore
```

The readiness tool is read-only and does not touch `/dev/shm`, OpenVINO, Qdrant, SQL, Scheduler, or EventBus.
