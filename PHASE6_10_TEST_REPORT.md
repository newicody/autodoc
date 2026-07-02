# Phase 6.10 test report — SourceCandidate Operator Bundle

## Scope

Phase 6.10 adds a local bundle writer for SourceCandidate operator reports.

The bundle contains a stable manifest and one or more local report artifacts derived from the existing operator report path.

## Commands

```bash
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src pytest -q tests/context/test_source_candidate_operator_bundle.py
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Expected result

- Targeted operator bundle tests pass.
- Rule tests pass.
- Full suite passes.

## code_rule_review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: Phase 6.10 only writes a local bundle derived from the existing operator report projection; no new architecture rule is required.
live_path_status: n/a
live_path_uses_real_backend: true
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
