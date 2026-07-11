# Phase 0272-r8 test report — ProjectV2 durable consumer

## Scope

- approved r7 gate validation ;
- existing SQL record builder reuse ;
- SQL insert-if-absent and mandatory readback ;
- immutable collision refusal ;
- idempotent replay ;
- laboratory-neutral durable metadata ;
- OpenVINO/Qdrant/GitHub/Scheduler/SHM boundaries closed.

## Review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: typed immutable command/plan/result and injected SQL effect reuse existing rules
live_path_status: transition
live_path_uses_real_backend: existing DB-API SQL store; SQLite local test binding
context_contract_version: missipy.github.project_v2_source_candidate_durable_consumer_report.v1
context_contract_changed: true
search_commands_bounded: n/a
non_stdlib_dependency_added: false
```

## Validation commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_project_v2_source_candidate_durable_consumer_0272.py \
  tests/tools/test_consume_github_project_v2_source_candidate_gate_0272.py
```

## Construction validation

```text
compileall added Python files: OK
git diff --check: OK
DOT syntax: checked when graphviz dot is available
full repository suite: to run on the target checkout at c8ec121
network calls in r8 tests: none
```
