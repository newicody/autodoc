# ProjectV2 parent/theme query normalization — 0282-r3

## Purpose

Extend the existing 0272 ProjectV2 query-only snapshot with the native
`Issue.parent` and bounded `Issue.subIssues(first: 100)` fields, then normalize
that snapshot into the immutable references introduced by 0282-r2.

GitHub added `Issue.parent` and `Issue.subIssues` to its GraphQL schema, and
Projects exposes parent/sub-issue hierarchy as built-in fields. This phase reads
those relationships; it does not mutate them.

## Reuse

```text
existing_query_extended: true
parallel_query_transport_added: false
r2_lineage_reference_builders_reused: true
append_only_ticket_revision_builder_reused: true
```

No second ProjectV2 client, fetcher, adapter or intake is introduced.

## Normalized item

```text
project_item_ref
issue_ref
parent_issue_ref
sub_issue_refs
theme_refs
theme_values
status_name
status_revision_ref
hierarchy_payload_present
```

Themes are selected from configured field names or field IDs. The defaults
recognize `Theme` and `Thème`. Status defaults recognize `Status` and
`Étape Status`.

The status revision is deterministic over:

```text
snapshot_ref
project item id
status field reference
status value
```

## Safety and completeness

- A strict policy requires `parent` and `subIssues` to be present in each Issue
  payload.
- A paginated `subIssues` connection with `hasNextPage=true` is rejected rather
  than silently truncated.
- Foreign-repository parent or sub-issue references are rejected.
- Duplicate items, sub-issues, themes and multiple status values are rejected.
- Draft issues and pull requests are ignored by default and can be forbidden by
  policy.

## Boundaries

```text
new_runtime_module_added: true
new_cli_added: false
new_adapter_added: false
github_api_client_added: false
graphql_mutation_added: false
github_mutation_performed: false
sql_write_added: false
qdrant_write_added: false
scheduler_modified: false
projects_repository_change_required: false
external_dependencies_added: false
```

The existing GraphQL live path uses the extended query. The normalizer itself is
pure and performs no network call.
