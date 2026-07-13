# Phase 0281-r4 report — pinned cached Copilot CLI runtime

## Result

The Autodoc templates now use:

```text
@github/copilot@1.0.70
actions/cache@v4
workflow-local complete npm prefix
installation only on exact cache miss
version verification
COPILOT_AUTO_UPDATE=false
```

The deployed workflow in `newicody/projects` must receive the same change.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: transition
external_dependency_added: false
external_dependency_existing: @github/copilot
external_dependency_version: 1.0.70
external_dependency_pinned: true
scheduler_modified: false
scheduler_run_modified: false
github_mutation_added: false
sql_write_added: false
qdrant_write_added: false
projects_repository_change_required: true
projects_repository_change_reason: deploy workflow and allow actions/cache@v4 in newicody/projects
```

The next phase is `0281-r5-operator-laboratory-advisory-projection`.
