# Phase 6.11 Test Report — SourceCandidate Operator Command Surface

## Scope

Unify existing SourceCandidate CLI adapters behind one operator command surface.

## Expected gate

```bash
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src pytest -q tests/context/test_source_candidate_operator_cli.py
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Code rule block

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: n/a
live_path_uses_real_backend: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
