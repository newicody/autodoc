# PHASE0144_TEST_REPORT

```text
phase: 0144-scheduler_vector_indexing_result_frame
code_rule_review: done
code_rule_update_required: true
code_rule_reason: adds result-frame reuse rule for vector indexing smoke.
live_path_status: transition
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```

Validation performed during patch build:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_scheduler_vector_indexing_result_frame_0144.py tests/rules/test_scheduler_vector_indexing_result_frame_0144_rule.py
# 8 passed
PYTHONPATH=src:. pytest -q tests/tools/test_scheduler_vector_indexing_smoke_0143.py tests/tools/test_scheduler_vector_indexing_result_frame_0144.py tests/rules/test_scheduler_vector_indexing_smoke_0143_rule.py tests/rules/test_scheduler_vector_indexing_result_frame_0144_rule.py
# 16 passed
```
