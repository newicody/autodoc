# Phase 0281-r6 report — controlled advisory Issue publication

## Result

A local controlled adapter can now render and publish the validated r5
advisory preview to the corresponding Issue.

The adapter defaults to preview-only and implements deterministic create,
replay and collision behavior.

## Validation

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_controlled_advisory_issue_publication_0281.py \
  tests/tools/test_publish_github_advisory_issue_comment_0281.py \
  tests/rules/test_github_controlled_advisory_issue_publication_0281_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: transition
context_contract_version: missipy.github.controlled_advisory_issue_publication.v1
external_dependencies_added: false
existing_external_tool_reused: gh
scheduler_modified: false
scheduler_run_modified: false
network_added_to_kernel: false
github_mutation_default: false
github_mutation_execute_gate: operator approve + policy id + exact plan digest
sql_write_added: false
qdrant_write_added: false
projects_repository_change_required: false
projects_repository_change_reason: local adapter publishes; workflow permissions remain unchanged
```

```text
newicody/projects: no Git-tracked modification required
workflow permissions remain unchanged
```

The next phase is `0281-r7-real-closed-loop-smoke`.
