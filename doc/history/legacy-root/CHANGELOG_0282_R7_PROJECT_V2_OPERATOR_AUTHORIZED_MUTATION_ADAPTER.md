# Changelog 0282-r7 — ProjectV2 operator-authorized mutation adapter

- Added one local adapter for the approved r5/r6 plans.
- Reused the existing `gh api` subprocess boundary.
- Kept preview as the default mode.
- Required exact digest confirmation for every executed plan.
- Added Issue creation, sub-issue linking, field creation/update and theme assignment execution.
- Kept Project view grouping manual.
- Added explicit partial-execution reporting.

```text
existing_gh_cli_boundary_reused: true
preview_is_default: true
exact_plan_digest_confirmation_required: true
new_cli_added: true
new_adapter_added: true
network_added: true
github_api_added: true
view_grouping_automated: false
scheduler_modified: false
projects_repository_change_required: false
external_dependencies_added: false
```
