# ProjectV2 parent/sub-ticket mutation plan — 0282-r5

## Purpose

Produce a deterministic and reviewable plan for the next ProjectV2 research
cycle without performing any GitHub mutation.

The plan consumes the validated append-only history from 0282-r4. It does not
reconstruct lineage in parallel and does not create a second history store.

```text
r4_history_reused: true
existing_idempotency_pattern_reused: true
```

The create/replay/collision structure follows the already-validated controlled
publication boundary from 0281, adapted to Issue creation and native sub-issue
linking.

## Planning model

```text
validated r4 history
+ explicit operator approval
+ current root/child Issue snapshots
+ next-cycle title and summary
        |
        v
deterministic marker and bounded body
        |
        +-- no matching Issue
        |      -> create_issue
        |      -> add_sub_issue (depends on create)
        |
        +-- matching unlinked Issue
        |      -> link_existing
        |
        +-- matching and linked Issue
        |      -> replay
        |
        +-- changed body/title, duplicate marker,
               foreign parent or inconsistent hierarchy
               -> collision
```

The planned child is attached to the original root Issue. The append-only
`previous_cycle_ref` keeps chronological lineage independently from the native
GitHub parent/sub-issue projection.

## Snapshot requirement

The planner requires current snapshots for:

- the root Issue and its `sub_issue_refs`;
- any Issue carrying the deterministic cycle marker;
- the candidate child's `parent_issue_ref`.

A one-sided relation is treated as a collision instead of guessing which side
is authoritative.

## Operations

The plan can contain only:

```text
create_issue
add_sub_issue
```

Each operation remains an intention with:

```text
github_mutation_allowed: false
github_mutation_performed: false
```

The future r7 adapter must replace a symbolic `github-planned-issue:*` reference
with the concrete Issue reference before executing the dependent link.

## Boundaries

```text
new_runtime_module_added: true
new_cli_added: false
new_adapter_added: false
graphql_query_added: false
graphql_mutation_added: false
github_mutation_performed: false
filesystem_write_added: false
sql_write_added: false
qdrant_write_added: false
scheduler_modified: false
projects_repository_change_required: false
external_dependencies_added: false
```
