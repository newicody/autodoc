# PHASE0141_R1_TEST_REPORT

```text
phase: 0141-r1-qdrant_collection_conflict_idempotent_fix
code_rule_review: done
code_rule_update_required: false
live_path_status: smoke
live_path_uses_real_backend: true
context_contract_changed: false
search_commands_bounded: n/a
```

Validation performed in patch build:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_qdrant_projection_operator_rest_smoke_0140.py tests/rules/test_qdrant_projection_operator_rest_smoke_0140_rule.py
```

Expected result:

```text
8 passed
```
