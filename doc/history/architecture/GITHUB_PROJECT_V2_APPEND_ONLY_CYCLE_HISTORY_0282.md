# ProjectV2 append-only cycle-history projection — 0282-r4

## Purpose

Compose the immutable lineage contract from r2 with the query-only normalized
ProjectV2 item from r3 into a deterministic local history.

```text
lineage result + normalized item + existing entries
-> validate existing chain and digests
-> append | replay | collision | reject
-> immutable projected history
```

## Append-only rules

1. The first entry has ordinal 1 and no `previous_cycle_ref`.
2. Each later entry has the same repository, project and root issue.
3. Ordinals are contiguous.
4. `previous_cycle_ref` targets the last existing cycle.
5. The normalized item must match lineage item, status, parent, sub-issues and
   themes.
6. Same `cycle_ref` and identical entry content is a replay.
7. Same `cycle_ref` with different content is a collision.
8. Existing entry digests are verified before accepting another cycle.
9. Source-artifact and decision references are bounded, non-empty and unique.

## Boundaries

```text
append_only_projection: true
new_runtime_module_added: true
new_cli_added: false
new_adapter_added: false
filesystem_write_added: false
network_added: false
github_api_added: false
graphql_mutation_added: false
github_mutation_performed: false
sql_write_added: false
qdrant_write_added: false
scheduler_modified: false
projects_repository_change_required: false
external_dependencies_added: false
```

The result is a projection contract, not a durable store. A later phase may
persist or publish a validated history only behind existing IO and authorization
boundaries.
