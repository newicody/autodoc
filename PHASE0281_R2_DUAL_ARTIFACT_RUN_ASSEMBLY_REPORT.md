# Phase 0281-r2 report — dual-artifact run assembly contract

## Result

Added an immutable local run-assembly use-case that recognizes the three
GitHub Actions artifact members, rejects duplicate/ambiguous members and reuses
the 0275 intake for correlation, digest validation and SourceCandidate creation.

The full Copilot advisory is retained in the intake result as a hint. The
SourceCandidate remains derived only from the authoritative request.

## Validation

```bash
PYTHONPATH=src:. python -m pytest -q   tests/context/test_github_dual_artifact_run_assembly_0281.py   tests/rules/test_github_dual_artifact_run_assembly_0281_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing immutable command/policy/result and reuse-before-new-module rules apply
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: missipy.github.dual_artifact_run_assembly.v1
context_contract_changed: true
external_dependencies_added: false
scheduler_modified: false
scheduler_run_modified: false
network_added: false
filesystem_write_added: false
github_api_added: false
github_mutation_added: false
sql_write_added: false
qdrant_write_added: false
projects_repository_change_required: false
projects_repository_change_reason: workflow already emits the expected names and filenames
```

The next phase is `0281-r3-fetch-once-run-group-integration` and will extend the
existing 0168 fetch surface rather than create a second fetcher.
