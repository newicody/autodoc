# Changelog 0282-r3 — ProjectV2 parent/theme query normalization

- Extended the existing ProjectV2 item query with `Issue.parent`.
- Added bounded `Issue.subIssues(first: 100)` query data.
- Added deterministic local normalization for parent, sub-issue, theme and
  status references.
- Reused 0282-r2 reference builders and append-only ticket revisions.
- Added explicit rejection of hierarchy truncation and foreign repositories.
- Added no parallel query transport, CLI, adapter or remote mutation.

```text
existing_query_extended: true
parallel_query_transport_added: false
new_runtime_module_added: true
new_cli_added: false
new_adapter_added: false
github_api_client_added: false
graphql_mutation_added: false
github_mutation_performed: false
scheduler_modified: false
projects_repository_change_required: false
external_dependencies_added: false
```
