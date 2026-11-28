# ProjectV2 operator-authorized mutation adapter — 0282-r7

## Purpose

Execute only the deterministic operations already approved in the 0282-r5 and
0282-r6 plans. Preview remains the default. Execution requires the explicit
operator decision `approve`, `--execute`, and exact confirmation of every plan
digest.

```text
existing_gh_cli_boundary_reused: true
preview_is_default: true
exact_plan_digest_confirmation_required: true
```

The adapter reuses the `gh api` subprocess boundary already established by
`publish_github_advisory_issue_comment_0281.py`. It does not add an HTTP client.

## Supported remote operations

```text
r5 create_issue
  -> REST POST repos/{repository}/issues

r5 add_sub_issue
  -> GraphQL addSubIssue

r6 field_create
  -> REST ProjectV2 field endpoint, API 2026-03-10

r6 field_update
  -> GraphQL updateProjectV2Field

r6 item_theme_assignment
  -> GraphQL updateProjectV2ItemFieldValue
```

The adapter resolves the created Issue node ID before linking it, and resolves
new field/option IDs before applying staged theme assignments. GraphQL calls use
versioned input objects so the plan remains separate from transport syntax.

## Failure behavior

- invalid, blocked or collision plans are refused;
- digest mismatch is refused before any mutation;
- GraphQL `errors` are treated as failures;
- partial execution is reported explicitly if an earlier operation succeeded;
- replay plans perform no mutation;
- view grouping is never automated.

## Boundaries

```text
new_cli_added: true
new_adapter_added: true
network_added: true
github_api_added: true
view_grouping_automated: false
scheduler_modified: false
sql_write_added: false
qdrant_write_added: false
projects_repository_change_required: false
external_dependencies_added: false
```
