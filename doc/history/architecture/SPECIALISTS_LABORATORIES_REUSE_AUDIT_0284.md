# Specialists and laboratories reuse audit — 0284-r1

## Existing chain selected

```text
laboratory_framework_contract_0273
→ deterministic_fake_laboratory_provider_0273
→ fake_laboratory_deliberation_composition_0274
→ fake_laboratory_recall_closed_result_frame_0274
→ fake_laboratory_closed_local_handoff_0274
→ fake_laboratory_existing_scheduler_closed_loop_smoke_0274
→ github_dual_artifact_laboratory_smoke_0275
```

No replacement laboratory framework is required.

```text
scheduler_remains_only_orchestrator: true
new_laboratory_manager_allowed: false
new_scheduler_allowed: false
new_parallel_queue_allowed: false
new_parallel_bus_allowed: false
event_bus_remains_observation_only: true
sql_remains_durable_authority: true
qdrant_remains_projection_and_recall: true
control_proxy_is_lateral_only: true
projects_repository_change_required: false
```

The next missing surface is a compact portable execution envelope binding:
`laboratory_ref`, `origin_laboratory_ref`, `target_laboratory_ref`, `visit_ref`,
`specialist_ref`, `conversation_ref`, `context_refs`, `return_route_ref`.

```text
0284-r2-specialist-portable-execution-envelope
```
