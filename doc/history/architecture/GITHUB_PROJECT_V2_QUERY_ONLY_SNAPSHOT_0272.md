# 0272-r3 — GitHub ProjectV2 query-only snapshot

## Decision

The canonical workflow source is the user ProjectV2 at
`https://github.com/users/newicody/projects/2` (view 2 is an operator/UI hint,
not a data authority).  The local server reads this Project directly through
GitHub GraphQL **query operations only** and writes an immutable local snapshot.

The Actions artifact path introduced by 0272-r2 remains available as a secondary
exchange mechanism.  It is no longer required for the local server to observe
the Project.

## Reuse audit

The implementation reuses:

- `github_project_push_frame_config` for validated owner, Project number,
  `token_env`, fcron-compatible scheduling fields and safety defaults;
- the existing operator convention of a gated scan-once command;
- stdlib `urllib.request` at the IO boundary, as no reusable ProjectV2 GraphQL
  query client exists in the repository.

No issue REST scanner, RuntimeManager, orchestrator, Scheduler modification or
new dependency is introduced.

## Flow

```text
GitHub user ProjectV2 newicody/2
-> GraphQL query-only fields pages
-> GraphQL query-only items pages
-> deterministic normalized snapshot
-> immutable local file under .var/github/project_v2/snapshots
-> typed report under .var/reports
```

The snapshot includes Project metadata, field definitions, Project items,
content for DraftIssue/Issue/PullRequest, and selected field values including
Status.  Stable GraphQL node IDs are preserved.

## Boundaries

- the query document is rejected if it contains a `mutation` operation;
- live execution requires a `policy_decision_id`;
- the token is read only from the configured environment variable and is never
  serialized;
- no GitHub write, workflow dispatch, SQL write, Qdrant write or SHM operation
  occurs;
- GitHub remains a workflow/review surface and the enriched authority remains
  local;
- the snapshot filename is content-addressed and existing snapshots are never
  overwritten with different content.
