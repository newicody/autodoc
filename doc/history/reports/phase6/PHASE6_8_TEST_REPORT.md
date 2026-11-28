# Phase 6.8 test report — SourceCandidate Operator Report CLI

## Scope

Adds a local operator report projection over the Phase 6.7 review-audit summary.

## Commands

```bash
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src pytest -q tests/context/test_source_candidate_operator_report.py
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Expected result

- targeted operator report tests pass
- rules pass
- full suite passes

## Code rule block

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: Phase 6.8 is an additive local projection over existing review/audit results; it does not introduce a new backend or kernel path.
live_path_status: green
live_path_uses_real_backend: true
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
