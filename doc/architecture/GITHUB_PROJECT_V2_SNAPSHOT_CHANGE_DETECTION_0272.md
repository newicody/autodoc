# GitHub ProjectV2 snapshot change detection — 0272-r4

## Purpose

Compare immutable snapshots produced by 0272-r3 without contacting GitHub.
The first snapshot becomes a baseline.  Later comparisons identify added,
removed, changed and unchanged Project items, field-definition changes and
Status transitions.

## Reuse decision

The patch reuses `SNAPSHOT_SCHEMA` and the immutable, content-addressed snapshot
format from `github_project_v2_query_only_snapshot_0272`.  No second ProjectV2
reader, GraphQL client, manager or orchestrator is introduced.

## Boundaries

- local JSON reads only;
- one immutable content-addressed change-set write at the CLI boundary;
- no GraphQL query or mutation;
- no GitHub token;
- no SQL or Qdrant write;
- no Scheduler, EventBus, PassiveSupervisor or SHM operation;
- GitHub remains a workflow/review surface and local state remains authoritative.

## Selection

With explicit `--previous-snapshot` and `--current-snapshot`, those paths are
compared.  Otherwise the newest one or two `project-v2-*.json` files are selected
by local modification time and name.  One snapshot yields a valid baseline.

## Outputs

- immutable `.var/github/project_v2/changes/project-v2-change-set-<digest>.json`;
- operator report `.var/reports/github_project_v2_snapshot_change_detection_0272.json`.
