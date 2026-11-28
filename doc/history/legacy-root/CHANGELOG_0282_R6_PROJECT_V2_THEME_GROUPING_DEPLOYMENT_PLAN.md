# Changelog 0282-r6 — ProjectV2 theme grouping deployment plan

- Added a pure plan for creating or reusing the `Thème` field.
- Added safe `updateProjectV2Field` planning with existing option IDs retained.
- Added staged item assignment plans using `updateProjectV2ItemFieldValue`.
- Added replay and collision handling for target view grouping.
- Kept view grouping as an explicit operator step.
- Added no transport client, adapter, CLI or remote mutation.

```text
field_stage_planned: true
assignment_stage_planned: true
view_grouping_stage_planned: true
view_grouping_automated: false
new_cli_added: false
new_adapter_added: false
github_mutation_performed: false
scheduler_modified: false
projects_repository_change_required: false
external_dependencies_added: false
```
