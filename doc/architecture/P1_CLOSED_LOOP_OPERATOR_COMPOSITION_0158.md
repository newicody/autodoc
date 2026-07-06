# 0158 — P1 closed-loop operator composition

## Decision

0158 closes P1 by composing the existing validated operator tools into a single
operator command:

```text
tools/run_p1_closed_loop_operator_smoke.py
```

This is not a new orchestrator, worker, backend, Scheduler runner or adapter.
It is an operator-only composition wrapper around existing surfaces.

## Manual proof

The manual 0158 smoke proved the complete chain:

```text
0145 local artifact vector indexing
-> 0148 SQL persistence handoff
-> 0149 SQLContextStore persistence record
-> 0150 SQLContextStore write surface audit
-> 0151/0152 DbApiSqlContextStore.upsert_record controlled write
-> SQL readback
```

Observed terminal facts:

```text
write_status: persisted
readback_ok: true
selected_store_class: DbApiSqlContextStore
selected_write_method: upsert_record
sql_ref: sql:artifact/vector-indexing/0158
point_id: qdrant-point:2b7a151cee3eb947
qdrant_rest_id: 3184c5b1-037c-5468-92bb-f65ced471985
```

## Reused surfaces

| Phase | Existing surface | Role |
| --- | --- | --- |
| 0145 | `tools/run_local_artifact_vector_indexing_runner.py` | artifact -> Scheduler/RouteProxy/vector result |
| 0148 | `tools/run_sql_persistence_handoff_smoke.py` | vector result -> SQL handoff |
| 0149 | `tools/run_sql_context_store_persistence_smoke.py` | handoff -> SQLContextStore record |
| 0150 | `tools/run_sql_context_store_write_surface_audit.py` | verify write method surface |
| 0151/0152 | `tools/run_sql_context_store_controlled_write_smoke.py` | DB-API write/readback through `DbApiSqlContextStore.upsert_record` |

## Boundary

0158 does not create:

- `SQLPersistenceWorker`
- `SQLOrchestrator`
- `LocalArtifactOrchestrator`
- `LocalVectorIndexingOrchestrator`
- `SchedulerOpenVINORunner`
- `VectorOpenVINOEmbeddingAdapter`
- `VectorQdrantProjectionAdapter`

0158 does not modify:

- Scheduler runtime
- RouteProxy runtime
- OpenVINO backend
- Qdrant adapter
- SQL context store authority

## Operator command

Dry-run plan:

```bash
python tools/run_p1_closed_loop_operator_smoke.py . --format markdown
```

Execute:

```bash
python tools/run_p1_closed_loop_operator_smoke.py . \
  --execute \
  --format json
```

The final output artifacts are:

```text
.var/smoke/artifacts/0158/p1_closed_loop_operator_result.json
.var/smoke/artifacts/0158/p1_closed_loop_operator_report.md
```

## P1 closure definition

P1 is closed when the composed operator result reports:

```text
status: ok
write_status: persisted
readback_ok: true
selected_store_class: DbApiSqlContextStore
selected_write_method: upsert_record
```

Qdrant remains a projection/recall index. SQL remains durable authority.
