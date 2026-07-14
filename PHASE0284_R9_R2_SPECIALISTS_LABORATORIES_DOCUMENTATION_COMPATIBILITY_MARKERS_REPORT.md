# Phase 0284-r9-r2 test report

## Cause

The first compatibility patch attempted to edit
`tests/rules/test_projects_installation_copilot_safe_default_0284_rule.py`.
That file differs in the operator working tree, so `git apply --check` rejected
the hunk before changing any file.

## Resolution

- Do not modify the divergent historical test.
- Restore the 0281 and 0282 compatibility markers in `doc/README_CURRENT.md`.
- Preserve `Version du guide : `0284-r1-r5`.` as an explicit historical marker
  in the cumulative installation guide while keeping the current declaration at
  `0284-r9`.
- Add a stable rule that distinguishes the current version declaration from the
  historical compatibility marker.

## Boundaries

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: documentation and executable-rule compatibility only
live_path_status: n/a
runtime_modified: false
scheduler_modified: false
sql_modified: false
qdrant_modified: false
openvino_modified: false
github_workflow_modified: false
projects_installation_modified: true
projects_installation_verified: true
external_dependencies_added: false
```

## Expected regression result

```text
test_three_requested_architecture_views_exist_and_are_linked: green
test_current_roadmap_locks_post_copilot_closed_loop: green
test_installation_starts_with_copilot_disabled: green
```
