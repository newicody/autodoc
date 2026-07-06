# PHASE0147_TEST_REPORT

```text
phase: 0147-dynamic_artifact_route_refs
code_rule_review: done
code_rule_update_required: true
code_rule_reason: artifact runner must derive Scheduler/RouteProxy refs from typed artifact inputs instead of keeping static smoke refs.
live_path_status: dynamic_refs
live_path_uses_real_backend: false
context_contract_version: artifact-route-refs-0147
context_contract_changed: true
search_commands_bounded: n/a
```

Validation performed in patch build:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_dynamic_artifact_route_refs_0147.py tests/rules/test_dynamic_artifact_route_refs_0147_rule.py
# 11 passed
PYTHONPATH=src:. pytest -q tests/tools/test_artifact_intake_contract_0146.py tests/tools/test_local_artifact_vector_indexing_runner_0145.py tests/tools/test_dynamic_artifact_route_refs_0147.py
# 14 passed
```
