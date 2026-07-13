# GitHub ProjectV2 cycle-lineage contract — 0282-r2

## Purpose

Define one immutable local contract for ProjectV2 research-cycle lineage before
query normalization or remote mutation planning.

The 0282-r1 reuse audit found no existing module carrying the complete lineage
surface. This module is therefore justified, but remains data-only.

```text
reuse_audit_completed: true
existing_suitable_module_found: false
new_runtime_module_added: true
```

## Reused authority

Issue references reuse `build_origin_frame_id()` from
`github_project_push_frame.py`. Status revisions continue to use the existing
`github-ticket-revision:*` append-only identity.

```text
github-frame:<repository>/issues/<number>
github-ticket-revision:<digest>
```

## Contract

```text
GitHubProjectV2CycleLineageCommand
  repository
  project_id
  project_item_ref
  root_issue_ref
  parent_issue_ref
  previous_cycle_ref
  cycle_ordinal
  status_revision_ref
  sub_issue_refs
  theme_refs
  result_issue_ref
  metadata

GitHubProjectV2CycleLineagePolicy
  require_parent_after_initial
  require_previous_cycle_after_initial
  allow_parent_on_initial_cycle
  max_cycle_ordinal
  max_sub_issue_refs
  max_theme_refs

GitHubProjectV2CycleLineageResult
  valid / issues
  cycle_ref
  lineage_digest
  normalized lineage
  locked boundaries
```

The cycle identity is a deterministic SHA-256 projection of the normalized
command. Replaying the same command produces the same result and `cycle_ref`.

## Boundaries

```text
new_cli_added: false
new_adapter_added: false
network_added: false
github_api_added: false
graphql_query_added: false
graphql_mutation_added: false
github_mutation_performed: false
sql_write_added: false
qdrant_write_added: false
scheduler_modified: false
projects_repository_change_required: false
external_dependencies_added: false
```

The module does not decide how GitHub sub-issues or Project fields are fetched
or changed. Those remain future adapter responsibilities.
