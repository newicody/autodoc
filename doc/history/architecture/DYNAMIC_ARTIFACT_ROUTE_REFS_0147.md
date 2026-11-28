# 0147 — Dynamic artifact route refs

0147 derives Scheduler command refs, RouteProxy request refs, result refs, and route namespaces from the typed artifact intake contract introduced in 0146.

The pure helper lives in:

```text
src/context/artifact_route_refs.py
```

It derives refs from:

```text
artifact_ref
vector_indexing_job_ref
```

Example:

```text
artifact_ref: artifact:local/0147/demo
vector_indexing_job_ref: vector-indexing-job:artifact/0147-demo
```

becomes:

```text
scheduler-command:artifact/local-0147-demo/job/artifact-0147-demo/embedding-request
vector-route:artifact/local-0147-demo/job/artifact-0147-demo/embedding-request
scheduler-command:artifact/local-0147-demo/job/artifact-0147-demo/indexing-result
vector-route:artifact/local-0147-demo/job/artifact-0147-demo/indexing-result
```

## Boundary

- `artifact_route_refs.py` is pure and performs no IO.
- It does not import Scheduler, RouteProxyRuntime, OpenVINO, Qdrant, or SQL clients.
- `tools/run_local_artifact_vector_indexing_runner.py` passes the derived refs to the existing Scheduler smoke tool.
- `tools/run_scheduler_vector_indexing_smoke.py` accepts explicit refs and namespaces but still does not modify `Scheduler.run()`.
- OpenVINO and Qdrant stay behind the already-existing operator tools and adapters.
- SQLContextStore remains durable authority.
- Qdrant remains projection/recall only.

## Why

0145/0146 proved the artifact path, but live logs still showed inherited refs such as `vector-route:smoke/0143/embedding-request` and `vector-route:smoke/0144/indexing-result`. 0147 removes those static smoke refs from the artifact path and makes each artifact/job traceable by its own refs.
