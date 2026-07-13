# Phase 0281-r5 report — operator/laboratory advisory projection

## Result

A validated Copilot advisory can now be projected into the existing
operator-approved fake laboratory path as a typed hint-only context.

The projection preserves the complete human-readable advisory fields for
operator and laboratory review, while the authoritative request and
SourceCandidate remain unchanged.

## Validation

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_operator_laboratory_advisory_projection_0281.py \
  tests/rules/test_github_operator_laboratory_advisory_projection_0281_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing 0275 intake/laboratory composition and 0274 Scheduler path are reused
live_path_status: transition
context_contract_version: missipy.github.operator_laboratory_advisory_projection.v1
context_contract_changed: true
external_dependencies_added: false
scheduler_modified: false
scheduler_run_modified: false
parallel_orchestrator_added: false
network_added: false
github_api_added: false
github_mutation_added: false
sql_surface_changed: false
qdrant_surface_changed: false
projects_repository_change_required: false
projects_repository_change_reason: newicody/projects already emits the validated advisory artifact
```

```text
newicody/projects: no modification required
```

The next phase is `0281-r6-controlled-advisory-issue-publication`.
That phase is expected to require a `newicody/projects` change only when the
controlled publication adapter is deployed with `issues: write`; the Autodoc
contract itself must remain gated and mutation-closed by default.
