# 0146 — Artifact intake contract

0146 defines a typed artifact intake contract before the artifact runner derives dynamic jobs and routes.

The contract is pure. It lives in `src/context/artifact_intake_contract.py` and carries only metadata:

```text
artifact_ref
artifact_kind
artifact_path
text_kind
sql_ref
collection
dimension
route_root
vector_indexing_job_ref
text
```

The local artifact runner now writes:

```text
artifact_input.md
artifact_intake_contract.json
artifact_vector_indexing_report.md
artifact_vector_indexing_report.json
```

## Boundary

- 0146 reuses `tools/run_local_artifact_vector_indexing_runner.py`.
- 0146 reuses the existing Scheduler/RouteProxy/vector smoke chain.
- 0146 does not activate dynamic route refs.
- 0147 will derive dynamic refs from `artifact_ref` and `vector_indexing_job_ref`.
- The contract is pure and does not import Scheduler, RouteProxy, OpenVINO, Qdrant, or SQL clients.
- Scheduler remains the orchestrator.
- SQLContextStore remains durable authority.
- Qdrant remains projection/recall only.

## Why before dynamic refs

The previous runner proved the local artifact path, but it still carried static smoke refs such as `0143` and `0144`. 0146 introduces the typed input envelope first. 0147 can then derive route refs and job refs from stable, explicit artifact fields instead of guessing from free text.
