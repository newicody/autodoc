# Phase 0283-r6 report — Qdrant real binding readiness

## Result

The 0283 real binding now exposes separate local and operational readiness.
Local readiness is side-effect free. Operational readiness performs one
explicit read-only collection metadata request and verifies that the current
384-dimensional Cosine target is compatible.

## Existing surfaces reused

```text
tools/check_qdrant_client_projection_executor_0271.py
tools/check_qdrant_sql_authority_scope_0271.py
src/inference/qdrant_real_binding_configuration_0283.py
src/inference/qdrant_scoped_executor_factory_0283.py
```

The older tools remain useful standalone diagnostics. The new contract composes
their runtime primitives with the target-collection compatibility check missing
from the live binding chain.

## Next phase

```text
0283-r7-qdrant-real-binding-preview-first-cli
```

The CLI must default to local preview, require an explicit flag for the live
readiness probe and require a separate explicit authorization for projection or
recall execution.

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: r6 reuses all existing configuration and dependency diagnostics and adds only the missing read-only collection compatibility surface
live_path_status: transition
live_path_uses_real_backend: true
context_contract_version: missipy.qdrant.real_binding_readiness.v1
context_contract_changed: true
search_commands_bounded: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
qdrant_write_performed: false
qdrant_search_performed: false
sql_read_performed: false
sql_write_performed: false
llm_or_openvino_added: false
architecture_preserved: true
existing_r2_configuration_reused: true
existing_r3_factory_inspection_reused: true
existing_dependency_inspection_reused: true
new_runtime_module_added: true
live_probe_is_explicit: true
live_probe_read_only: true
collection_created: false
collection_updated: false
collection_deleted: false
qdrant_started: false
new_qdrant_executor_added: false
new_transport_added: false
control_proxy_integrated: false
event_bus_integrated: false
shm_or_mmio_integrated: false
projects_repository_change_required: false
```

`live_path_uses_real_backend` is true only when the caller explicitly requests
the live probe. Patch validation uses injected fakes and performs no network
request.
