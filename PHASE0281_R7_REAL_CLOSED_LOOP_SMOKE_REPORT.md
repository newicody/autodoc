# Phase 0281-r7 report — real closed-loop smoke

## Result

The 0281 chain now has a runnable local entrypoint that consumes the three real
GitHub Actions artifacts and writes the exact `publication_preview.json`
required by r6.

The entrypoint also writes the r6 publication plan but does not execute it.

## Validation

```bash
PYTHONPATH=src:. python -m pytest -q   tests/context/test_github_real_closed_loop_smoke_0281.py   tests/tools/test_run_github_real_closed_loop_smoke_0281.py   tests/rules/test_github_real_closed_loop_smoke_0281_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: transition
context_contract_version: missipy.github.real_closed_loop_smoke.v1
external_dependencies_added: false
existing_scheduler_reused: true
scheduler_modified: false
scheduler_run_modified: false
laboratory_scheduler_added: false
parallel_orchestrator_added: false
network_fetch_added: false
github_mutation_added: false
github_mutation_performed: false
sql_adapter_reused: SQLiteSqlContextStore
qdrant_adapters_reused: deterministic demo projection and recall
projects_repository_change_required: false
projects_repository_change_reason: newicody/projects already emitted all required artifacts
```

```text
newicody/projects: no Git-tracked modification required
```

The next step after this patch is an operator-run real smoke on run
`29246131317`, followed by r6 preview and explicit publication confirmation.
