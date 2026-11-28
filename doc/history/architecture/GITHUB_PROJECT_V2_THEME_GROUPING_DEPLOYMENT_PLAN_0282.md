# ProjectV2 theme-grouping deployment plan — 0282-r6

## Purpose

Produce a deterministic plan for deploying the `Thème` single-select field,
assigning theme values to Project items and grouping the target view by that
field.

The plan has three explicit stages:

```text
field_stage_planned: true
assignment_stage_planned: true
view_grouping_stage_planned: true
view_grouping_automated: false
```

## Field stage

When the field is absent, the plan describes the GitHub REST endpoint for
adding a single-select field to a user- or organization-owned ProjectV2.

When the field exists and its options differ, the plan describes
`updateProjectV2Field`. Existing option IDs are retained in
`singleSelectOptions`, preventing existing item values from being cleared.

The plan never executes either operation.

## Assignment stage

Each symbolic r3 Project item reference is paired with a desired theme name.
If field and option IDs already exist, the plan can describe a concrete
`updateProjectV2ItemFieldValue` input. Otherwise the operation remains staged
until the field creation/update response resolves those IDs.

## View grouping stage

GitHub's documented Project interface supports grouping a view by a custom
field. This phase records whether the target view is already grouped by the
theme field, conflicts with another grouping, or requires an operator to:

```text
View
→ Group by
→ Thème
→ Save changes
```

No automated view mutation is introduced.

## Decisions

```text
field absent                         -> create_field
field exact                          -> reuse_field
field options extended/changed       -> update_field
duplicate name / wrong type / loss   -> collision

view grouped by exact field          -> replay
view ungrouped or unknown            -> manual_grouping_required
view grouped by another field        -> view_collision
```

## Boundaries

```text
new_cli_added: false
new_adapter_added: false
external_dependencies_added: false
network_added: false
github_api_added: false
rest_mutation_allowed: false
graphql_mutation_allowed: false
github_mutation_performed: false
view_grouping_automated: false
sql_write_added: false
qdrant_write_added: false
scheduler_modified: false
projects_repository_change_required: false
```
