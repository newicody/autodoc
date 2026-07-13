# Phase 0279-r1 report — Copilot advisory response extraction

Scope: make the existing optional GitHub Copilot advisory adapter consume the
CLI structured JSONL response and produce the third dual-artifact output.

Validation commands:

```bash
PYTHONPATH=src:. python -m compileall -q templates/github/scripts tests/tools
PYTHONPATH=src:. pytest -q \
  tests/tools/test_github_copilot_advisory_response_extraction_0279.py \
  tests/rules/test_copilot_advisory_response_extraction_0279_rule.py \
  tests/rules/test_github_dual_artifact_actions_workflow_0275_rule.py \
  tests/tools/test_github_copilot_advisory_optional_0277.py
```

Expected live validation:

```text
autodoc-authoritative-request
autodoc-copilot-advisory
autodoc-dual-artifact-manifest
```

Phase review:

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing adapter and effect-boundary rules already cover the change
live_path_status: transition
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
stdlib_only: true
scheduler_modified: false
scheduler_run_modified: false
graph_update_required: false
```
