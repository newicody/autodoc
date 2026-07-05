# PHASE0114_R2_TEST_REPORT

```text
phase: 0114-r2-context_variation_core_contract
code_rule_review: done
code_rule_update_required: false
code_rule_reason: pure context contracts; no backend runtime import; no kernel loop modification.
live_path_status: transition
live_path_uses_real_backend: n/a
context_contract_version: missipy.context.v1
context_contract_changed: true
search_commands_bounded: true
```

Expected validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_context_variation_core_contract.py
PYTHONPATH=src:. pytest -q tests/rules/test_context_variation_core_contract_0114_r2_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
