# 0145 — Local artifact vector indexing runner

0145 turns the validated Scheduler/RouteProxy/vector smoke into a local artifact runner.

The runner is an operator surface, not a new orchestrator. It reuses tools/run_scheduler_vector_indexing_smoke.py and wraps it with a local artifact input and local artifact result envelope.

## Flow

```text
artifact text
-> artifact_input.md
-> tools/run_scheduler_vector_indexing_smoke.py
-> existing Scheduler route handler
-> existing RouteProxyRuntime request frame
-> existing local vector indexing smoke
-> tools/embed_e5.py --format json --full-vector
-> tools/run_qdrant_projection_live_smoke.py --vector-json
-> existing RouteProxyRuntime vector_indexing_result frame
-> artifact_vector_indexing_report.md/json
```

## Output files

It writes artifact_input.md, artifact_vector_indexing_report.md, and artifact_vector_indexing_report.json.

Default location:

```text
.var/smoke/artifacts/0145/
```

## Boundaries

- Scheduler remains the orchestrator.
- RouteProxyRuntime remains the frame IO surface.
- OpenVINO and Qdrant remain behind existing tools and adapters.
- SQLContextStore remains durable authority.
- Qdrant stores projection and recall indexes only.
- No Scheduler.run() change in 0145.
- No new OpenVINO adapter is created.
- No new Qdrant adapter is created.
- No LocalVectorIndexingOrchestrator is created.
- No LocalArtifactOrchestrator is created.

## Why this exists

0144 already proves a Scheduler-shaped command can create a request frame, execute strict OpenVINO/Qdrant vector indexing, and write a result frame. 0145 packages that as a local artifact envelope so the next phase can accept a real local markdown/json artifact without inventing a new orchestration layer.

## Phase status

```text
code_rule_review: done
code_rule_update_required: true
code_rule_reason: artifact runner boundary is now locked to prevent new orchestrator wheels.
live_path_status: smoke
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
