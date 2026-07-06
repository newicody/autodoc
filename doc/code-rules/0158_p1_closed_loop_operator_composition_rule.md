# Code rule — 0158 P1 closed-loop operator composition

0158 may add one operator composition tool:

```text
tools/run_p1_closed_loop_operator_smoke.py
```

## Required behavior

The tool must compose existing surfaces in this order:

```text
0145 local artifact vector indexing runner
0148 SQL persistence handoff
0149 SQLContextStore persistence record
0150 SQLContextStore write surface audit
0151/0152 DbApiSqlContextStore.upsert_record controlled write/readback
```

## Required final proof

The closed-loop result must expose:

```text
write_status
readback_ok
selected_store_class
selected_write_method
sql_ref
point_id
qdrant_rest_id
```

## Forbidden

Do not create or introduce:

- `SQLPersistenceWorker`
- `SQLOrchestrator`
- `LocalArtifactOrchestrator`
- `LocalVectorIndexingOrchestrator`
- `SchedulerOpenVINORunner`
- `VectorOpenVINOEmbeddingAdapter`
- `VectorQdrantProjectionAdapter`

Do not modify Scheduler, RouteProxy, OpenVINO, Qdrant or SQL authority runtime
code for this phase.

## Boundary

0158 is an operator composition layer only.

It may call existing tools through subprocess boundaries. It must not import
OpenVINO, Qdrant clients, or database-specific backend clients directly.

SQL remains durable authority. Qdrant remains projection/recall metadata.
