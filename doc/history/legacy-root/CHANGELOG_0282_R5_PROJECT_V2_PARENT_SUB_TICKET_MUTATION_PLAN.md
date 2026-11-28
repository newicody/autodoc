# Changelog 0282-r5 — ProjectV2 parent/sub-ticket mutation plan

- Added a pure immutable next-cycle Issue/sub-issue plan.
- Reused the 0282-r4 append-only history as the lineage authority.
- Added deterministic cycle markers and bounded Issue bodies.
- Added `create_and_link`, `link_existing`, `replay`, `collision` and `blocked`
  outcomes.
- Added collision detection for duplicate markers, changed content, foreign
  parents, closed Issues and inconsistent two-sided hierarchy snapshots.
- Added no CLI, transport, adapter or GitHub mutation.

```text
r4_history_reused: true
existing_idempotency_pattern_reused: true
new_runtime_module_added: true
new_cli_added: false
new_adapter_added: false
graphql_query_added: false
graphql_mutation_added: false
github_mutation_performed: false
scheduler_modified: false
projects_repository_change_required: false
external_dependencies_added: false
```
