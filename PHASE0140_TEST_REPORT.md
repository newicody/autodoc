# PHASE0140_TEST_REPORT

```text
phase: 0140-qdrant_projection_operator_rest_smoke
code_rule_review: done
code_rule_update_required: true
code_rule_reason: live Qdrant REST smoke is allowed only in the operator tool; Scheduler/RouteProxy/context contracts remain outside Qdrant.
live_path_status: smoke
live_path_uses_real_backend: true_when_execute_is_used
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```

Validation performed in patch build:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_qdrant_projection_operator_rest_smoke_0140.py tests/rules/test_qdrant_projection_operator_rest_smoke_0140_rule.py
# 10 passed
```
