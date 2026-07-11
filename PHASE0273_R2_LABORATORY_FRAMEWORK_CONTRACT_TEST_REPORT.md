# Phase 0273-r2 test report — laboratory framework contract

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_laboratory_framework_contract_0273.py
PYTHONPATH=src:. python -m pytest -q
```

## Covered behavior

- immutable and JSON-serializable descriptors;
- explicit bounded budgets;
- same-laboratory defaults;
- mediated cross-laboratory identity;
- context/evidence limit enforcement;
- deeply frozen machine results;
- request/result identity and budget validation;
- external laboratory request rejection without network budget;
- inactive binding plan targeting the existing 0257 registry;
- rejection of parallel manager/registry/Scheduler/EventBus ownership.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing immutable-contract, kernel-convergence, resource-bound and reuse rules apply
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: missipy.laboratory.v1
context_contract_changed: true
external_dependencies_added: false
scheduler_modified: false
provider_active: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
