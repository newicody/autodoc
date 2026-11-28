# GitHub scan-once handoff - 0267

## Intent

0267 prepares a local scan-once handoff artifact from the closed frame and the PassiveSupervisor report:

```text
0264 closed ResultFrame + 0266 PassiveSupervisor report -> GitHub scan-once handoff
```

local/server remains the authority. GitHub is a review/workflow surface, not the authority.

## Boundary

remote mutation is forbidden in 0267.

This patch does not call the GitHub API. It does not create issues, update projects, push commits, open pull requests, poll GitHub, start services, or modify Scheduler.run.

scan-once means one local artifact envelope, no polling loop.

## Existing surfaces acknowledged

The repository already contains GitHub-oriented context surfaces such as `github_project_push_frame`, `github_publication_review`, `source_candidate_github_adapter`, and `source_candidate_remote_mutation_gate`. 0267 does not replace them. It prepares a local envelope that can later be connected through a controlled gate.

## Output

The handoff contains `handoff_ref`, `repository`, `sql_ref`, `embedding_ref`, `source_reports`, `summary`, `passive_findings`, `github_actions`, and `remote_mutation_allowed=False`.

## Next step

0268 can prepare OpenRC/launcher minimal readiness without starting external services from Scheduler.
