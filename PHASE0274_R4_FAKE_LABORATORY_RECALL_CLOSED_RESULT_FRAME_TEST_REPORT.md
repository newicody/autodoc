# Phase 0274-r4 test report — fake laboratory recall closed ResultFrame

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_fake_laboratory_recall_closed_result_frame_0274.py
PYTHONPATH=src:. python -m pytest -q
```

## Covered behavior

- dry-run creates no query, recall, rehydrate or observation effect;
- query and passage profiles share one E5 space while retaining their roles;
- Qdrant returns refs and SQL rehydrates the exact specialist output;
- 0264 builds a valid closed ResultFrame;
- 0265 facts publish through an injected existing EventBus only;
- 0266 and visual models remain passive;
- missing or wrong recalled output blocks frame creation;
- profile mismatch blocks before OpenVINO and Qdrant recall;
- GitHub mutation remains closed.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: missipy.laboratory.v1
context_contract_changed: false
external_dependencies_added: false
scheduler_created: false
scheduler_modified: false
parallel_orchestrator_created: false
parallel_eventbus_created: false
parallel_registry_created: false
sql_write_performed: false
qdrant_write_performed: false
qdrant_recall_refs_only: true
sql_rehydrate_performed: true
eventbus_observation_only: true
provider_active: true
github_mutation_performed: false
network_added: false
```
