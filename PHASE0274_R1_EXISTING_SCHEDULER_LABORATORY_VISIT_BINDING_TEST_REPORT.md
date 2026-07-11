# Phase 0274-r1 test report — existing Scheduler laboratory visit binding

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_scheduler_laboratory_visit_binding_0274.py
PYTHONPATH=src:. python -m pytest -q
```

## Covered behavior

- event targets `scheduler`;
- Handler rejects wrong event type or payload;
- provider executes behind the existing Handler boundary;
- Handler registration uses the existing Dispatcher;
- live request passes through the existing Scheduler;
- the Dispatcher publishes only its observation copy;
- r3 follow-up scenarios survive the Scheduler path;
- submission without the existing Scheduler running fails by timeout;
- receipt remains JSON serializable and records no parallel authority.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing single-Scheduler, immutable Event, Handler and passive EventBus rules are reused
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: missipy.laboratory.v1
context_contract_changed: false
external_dependencies_added: false
scheduler_created: false
scheduler_modified: false
scheduler_run_modified: false
parallel_queue_created: false
parallel_eventbus_created: false
parallel_registry_created: false
provider_active: true
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
```
