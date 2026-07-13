# Phase 0281-r3 report — fetch-once run-group integration

## Result

The existing 0168 `--sync-tool` extension point now has a concrete adapter that
preserves the existing 0167 raw sync and then invokes the 0281-r2/0275
run-level intake path over sibling staging directories.

The complete Copilot advisory becomes locally recoverable from the stable
run-group report. It remains explicitly non-authoritative.

## Validation

```bash
PYTHONPATH=src:. python -m pytest -q   tests/tools/test_github_dual_artifact_server_sync_once_0281.py   tests/rules/test_github_dual_artifact_fetch_run_group_integration_0281_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing adapter port and reuse-before-new-runtime rules apply
live_path_status: transition
live_path_uses_real_backend: true
context_contract_version: missipy.github.dual_artifact_fetch_run_group.v1
context_contract_changed: true
external_dependencies_added: false
scheduler_modified: false
scheduler_run_modified: false
network_added: false
filesystem_read_added: true
filesystem_write_added: true
filesystem_write_scope: local idempotent run-group report
github_api_added: false
github_mutation_added: false
sql_write_added: false
qdrant_write_added: false
projects_repository_change_required: false
projects_repository_change_reason: deployed workflow already emits the locked artifact names and filenames
local_operator_change_required: true
local_operator_change_reason: select the adapter with --sync-tool tools/run_github_dual_artifact_server_sync_once_0281.py
```

The next phase is `0281-r4-pinned-cached-copilot-cli-runtime`.

That next phase **will require a modification in `newicody/projects`**, because
the deployed workflow must use the cached/pinned CLI and the selected-actions
policy must allow the chosen GitHub-owned cache action.
