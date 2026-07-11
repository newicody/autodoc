# Phase 0274-r5 test report — fake laboratory existing-Scheduler closed-loop smoke

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_fake_laboratory_existing_scheduler_closed_loop_smoke_0274.py
PYTHONPATH=src:. python -m pytest -q
```

## Covered behavior

- complete r2 -> r3 -> r4 semantic closure;
- one existing Scheduler supplied by the caller;
- SQL specialist-output persistence and exact recall/rehydration;
- passage/query profile continuity;
- closed ResultFrame identity;
- passive supervision and visual-model completeness;
- gated local GitHub preview;
- immutable SQL replay without replacement or second vector write;
- fact publication through the existing EventBus;
- early stop on incomplete deliberation;
- failure on wrong recall reference.

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
scheduler_run_owned: false
parallel_orchestrator_created: false
parallel_queue_created: false
parallel_eventbus_created: false
parallel_registry_created: false
sql_replay_verified: true
provider_active: true
github_mutation_performed: false
network_added: false
```
