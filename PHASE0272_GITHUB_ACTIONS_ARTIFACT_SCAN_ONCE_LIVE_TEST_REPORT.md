# Phase 0272-r2 test report

## Result

0272-r2 binds the already-existing Project/Action configuration, GitHub Actions
artifact fetch and local server dataset sync into one gated scan-once. It does not
scan issues directly and does not add a GitHub transport.

## Review block

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing typed-contract, reuse-before-new-module and IO-boundary rules are sufficient
live_path_status: opt-in
live_path_uses_real_backend: existing GitHubActionsClient
context_contract_version: missipy.github_actions.artifact_scan_once_live.v1
context_contract_changed: true
external_dependencies_added: false
scheduler_modified: false
network_added: false
network_reused: existing 0168 GET/download only
github_api_added: false
direct_issue_scan_added: false
workflow_dispatch_allowed: false
remote_mutation_allowed: false
sql_or_qdrant_write_added: false
search_commands_bounded: true
```

## Validation performed

```text
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/context/test_github_actions_artifact_scan_once_live_0272.py
PYTHONPATH=src:. python -m pytest -q tests/tools/test_run_github_actions_artifact_scan_once_live_0272.py
PYTHONPATH=src:. python -m pytest -q tests/rules/test_github_actions_artifact_scan_once_live_0272_rule.py
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

Fixture mode is offline. Live mode reads the token from the configured environment
variable, reuses the existing read-only client, and serializes no secret value.

## Construction result

```text
base_commit: 740d1d36ea312f97b7f6db6684cfe7bca92f2d33
compileall_targeted: passed
targeted_tests: 14 passed
graphviz_dot: passed
network_used_by_tests: false
remote_mutation_performed: false
```
