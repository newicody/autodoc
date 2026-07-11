# 0272-r1 — GitHub real read-only scan reuse audit

## Decision

The repository already contains reusable GitHub boundaries:

- `GitHubActionsClient` performs authenticated GET/download operations for GitHub Actions artifacts;
- `github_artifact_server_fetch_config` already validates `token_env`, rejects literal secrets and maintains `allowed_repositories`;
- 0267 provides the local scan-once handoff and keeps `remote_mutation_allowed=False`;
- `source_candidate_remote_mutation_gate` is the explicit remote mutation gate;
- `source_candidate_github_adapter` is fake-only and mutation-facing, so it is not the read path.

The issue scan client is absent from the current repository. No existing surface implements a bounded
`list_repository_issues` operation. A small shared read-only IO membrane is therefore
justified for 0272-r2, but it must reuse the existing token-env, API URL, allow-list and
0267 handoff boundaries instead of introducing a second configuration model.

## Boundaries

0272-r1 is source inspection only. It performs no GitHub API request, no token read, no
remote mutation, no polling, no SQL/Qdrant write and no Scheduler modification.

The later live scan remains one-shot and bounded. GitHub stays a review/workflow surface;
the local/server store remains authoritative.
