# Phase 0284-r1-r2 — Autodoc / Projects boundary realignment

## Result

The repository boundary is realigned so that Autodoc no longer exposes the
Projects management workflow or Project-oriented Issue forms as active
repository features.

The reusable bundle remains under:

```text
templates/github/projects-repository/
```

It is intended to be copied to `newicody/projects`, which owns its views,
workflows, forms, variables and secrets.

## Audit conclusion

The ProjectV2 source, intake, dispatch and controlled-publication modules are
not a Project mode. They are explicit external connector adapters and remain
valid when they preserve local authority and explicit mutation gates.

A separate configuration migration is still required because the query-only
example currently carries historical outbound workflow-dispatch parameters.
That migration is intentionally not folded into this cleanup patch.

## Phase review

```yaml
live_path_status: n/a
live_path_uses_real_backend: n/a
scheduler_modified: false
new_runtime_service: false
new_bus: false
new_orchestrator: false
network_access_added: false
github_api_access_added: false
github_remote_mutation_added: false
sql_write_added: false
qdrant_write_added: false
openvino_execution_added: false
llm_execution_added: false
projects_repository_change_required: true
projects_repository_change_kind: copy-source-boundary-only
```

## Next boundary patches

1. `0284-r1-r3-github-project-connector-config-split`
2. `0284-r1-r4-projects-repository-copilot-views`
3. resume `0284-r2-portable-specialist-contract`
