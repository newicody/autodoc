# 0157 — P1 single runner surface audit

## Decision

P1 must reuse the existing local artifact runner:

```text
tools/run_local_artifact_vector_indexing_runner.py
```

It is the correct base for the P1 single runner because it already wraps the
validated Scheduler/RouteProxy/vector smoke path and remains an operator surface,
not a new orchestrator.

## Evidence

The 0157 rule audit passed the P1 rule set from 0143 to 0152.

Validated rule families:

- 0143 Scheduler vector indexing smoke
- 0144 Scheduler vector indexing result frame
- 0145 Local artifact vector indexing runner
- 0146 Artifact intake contract
- 0147 Dynamic artifact route refs
- 0148 SQL persistence handoff
- 0149 SQL context store persistence smoke
- 0150 SQL context store write surface audit
- 0151 SQL context store controlled write
- 0152 SQL context store configured DB path

## Existing surfaces to reuse

| Phase | Surface | Decision |
| --- | --- | --- |
| 0145 | `tools/run_local_artifact_vector_indexing_runner.py` | Reuse as P1 operator runner base. |
| 0146 | `src/context/artifact_intake_contract.py` | Reuse typed artifact intake. |
| 0147 | `src/context/artifact_route_refs.py` | Reuse dynamic route refs. |
| 0148 | `tools/run_sql_persistence_handoff_smoke.py` | Reuse handoff builder. |
| 0149 | SQLContextStore persistence record | Reuse persistence record shape. |
| 0151 | `DbApiSqlContextStore.upsert_record` | Reuse existing durable SQL write. |
| 0152 | configured SQL context DB path | Reuse DB path precedence. |

## Boundary

0157 does not create runtime code.

Forbidden in 0157 and next P1 closure work unless a later audit explicitly
proves necessity:

- `LocalArtifactOrchestrator`
- `LocalVectorIndexingOrchestrator`
- `SchedulerOpenVINORunner`
- `SQLPersistenceWorker`
- `SQLOrchestrator`
- `VectorOpenVINOEmbeddingAdapter`
- `VectorQdrantProjectionAdapter`

## Missing closure

The remaining P1 gap is composition, not new architecture.

The missing command is:

```text
local artifact
-> 0145 artifact vector indexing runner
-> 0148 SQL persistence handoff
-> 0149 SQLContextStore persistence record
-> 0151/0152 controlled SQL write/readback
-> final P1 report
```

## Next

0158 should compose the existing tools into a single P1 closed-loop operator
command. It must not create a new Scheduler runner, SQL worker, OpenVINO adapter,
Qdrant adapter, or orchestrator.
