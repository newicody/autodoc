# PHASE0138_TEST_REPORT

```text
phase: 0138-openvino_e5_live_smoke_existing_path
code_rule_review: done
code_rule_update_required: true
code_rule_reason: add live smoke rule that executes E5/OpenVINO only through existing tools/embed_e5.py and existing inference membranes.
live_path_status: smoke-ready
live_path_uses_real_backend: optional-via---execute
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```

Validation performed in patch build:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_openvino_e5_live_smoke_existing_path_0138.py tests/rules/test_openvino_e5_live_smoke_existing_path_0138_rule.py
# 8 passed
```

0138 does not execute the backend during pytest. Backend execution requires `--execute`.
