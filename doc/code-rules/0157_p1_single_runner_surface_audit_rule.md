# Code rule — 0157 P1 single runner surface audit

0157 is audit-only.

## Required decision

P1 closure must reuse:

```text
tools/run_local_artifact_vector_indexing_runner.py
```

as the existing local artifact runner surface.

## Required reuse chain

Future P1 closure work must compose existing surfaces:

```text
0145 local artifact vector indexing runner
0146 artifact intake contract
0147 dynamic artifact route refs
0148 SQL persistence handoff
0149 SQLContextStore persistence record
0151/0152 DbApiSqlContextStore.upsert_record write/readback
```

## Forbidden

Do not create:

- `LocalArtifactOrchestrator`
- `LocalVectorIndexingOrchestrator`
- `SchedulerOpenVINORunner`
- `SQLPersistenceWorker`
- `SQLOrchestrator`
- `VectorOpenVINOEmbeddingAdapter`
- `VectorQdrantProjectionAdapter`

## Boundary

0157 may add docs, changelog, manifest, test report and a runtime DOT only.
It must not modify runtime Python files.
