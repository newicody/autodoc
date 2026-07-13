# GitHub ProjectV2 cycle history reuse audit — 0282-r1

## Goal

Audit the existing ProjectV2, ticket-artifact and append-only-history surfaces
before implementing cycle history, parent/sub-ticket relationships or theme
grouping.

This phase is documentation and executable architecture review only. It adds no
runtime, CLI, adapter, GraphQL operation or GitHub mutation.

## Existing surfaces to reuse

| Existing surface | Reuse decision |
|---|---|
| `github_project_v2_query_only_snapshot_0272.py` | retain as the read-only ProjectV2 field/item source |
| `github_project_v2_snapshot_change_detection_0272.py` | extend later to derive cycle transitions from immutable snapshots |
| `github_project_v2_change_handoff_0272.py` | retain SourceCandidate handoff instead of creating a second intake |
| `github_project_v2_en_cours_dispatch_0275_r8.py` | retain the idempotent `En cours` dispatch boundary |
| `github_project_push_frame.py` | reuse append-only ticket revisions and user decisions as the history base |
| `github_project_scenario.py` | reuse scenario composition for board-level projection |
| `github_action_ticket_artifact.py` | reuse ticket artifact identity and correlation |

## Missing capability

No current runtime surface explicitly models all of:

```text
cycle_ref
previous_cycle_ref
root_issue_ref
parent_issue_ref
sub_issue_refs
theme_refs
project_item_ref
status_revision_ref
result_issue_ref
```

This does not justify a manager, registry or parallel orchestrator.

## GitHub-native representation

The selected design uses native sub-issues for cycle lineage and a dedicated
Project field for theme grouping. Parent/sub-issue hierarchy remains the
relationship authority; theme grouping remains a board projection.

## Proposed 0282 sequence

```text
0282-r1  reuse audit
0282-r2  immutable local cycle-lineage contract
0282-r3  query-only parent/theme normalization
0282-r4  append-only cycle-history projection
0282-r5  parent/sub-ticket mutation plan only
0282-r6  theme/grouping deployment plan only
0282-r7  explicit operator-authorized adapter
0282-r8  real ProjectV2 cycle-history smoke
```

## Locked boundaries

```text
runtime_source_modified: false
new_runtime_module_added: false
new_cli_added: false
new_adapter_added: false
graphql_query_added: false
graphql_mutation_added: false
github_mutation_performed: false
sql_write_added: false
qdrant_write_added: false
scheduler_modified: false
projects_repository_change_required: false
external_dependencies_added: false
```

The Scheduler remains the sole Autodoc orchestration authority. ProjectV2 is a
workflow and review surface, not the durable authority.
