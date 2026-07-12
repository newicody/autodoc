# Phase 0275-r6 test report — GitHub research Kanban operator model

## Scope

Documentation and executable rules only.

## Reuse audit

The phase records mandatory reuse of the existing ProjectV2 query-only reader,
snapshot diff, SourceCandidate handoff, GitHub artifact builders, artifact
fetch-once path, attachment surfaces, Scheduler boundary and SQL authority.

No new runtime module is introduced.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. python -m pytest -q \
  tests/rules/test_github_research_kanban_operator_model_0275_r6_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules

PYTHONPATH=src:. python -m pytest -q
```

## Mandatory phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: phase documentaire conforme aux frontières existantes
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
non_stdlib_dependencies_added: false
scheduler_modified: false
scheduler_run_modified: false
remote_mutation_added: false
runtime_modified: false
openrc_service_added: false
```
