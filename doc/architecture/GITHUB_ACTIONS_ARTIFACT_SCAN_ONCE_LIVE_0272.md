# 0272-r2 — GitHub Actions artifact scan-once live binding

## Decision

0272 does not add a direct issue scanner. The ticket or Project event is handled
inside the external repository by a GitHub Action. That Action emits append-only
GitHub Actions artifacts. The local server then performs one bounded GET/download
pass over those artifacts.

The live binding reuses:

- `github_project_push_frame_config` for Project, workflow, token-env and safety configuration;
- `github_artifact_server_fetch_config` for the server dataset and allow-list;
- `tools/run_github_actions_artifact_fetch_once.py` for the existing 0168 GET/download transport;
- `tools/run_github_artifact_server_sync_once.py` for the existing 0167 raw/index/history/conversion-queue sync.

No new GitHub client, issue API adapter, Project GraphQL scanner, polling loop,
runtime manager or Scheduler authority is introduced.

## Flow

```text
GitHub issue / Project-facing event
  -> GitHub Action in the external idea repository
  -> append-only GitHub Actions artifact
  -> existing 0168 GET/download fetch
  -> existing 0167 local server dataset sync
  -> raw / index / history / conversion_queue / VisPy observation
```

The local scan is one-shot and bounded by `max_runs` and `max_artifacts`. The
existing state file makes repeated scans idempotent by skipping already-synced
artifact keys. The example fcron command carries an explicit stable read-only
`policy_decision_id`; the CLI keeps `--config` as the 0165-compatible alias.

## Gates

Live execution requires an explicit `policy_decision_id`. The token value is read
only by the existing fetch boundary from the configured environment variable. The
0272 report contains the environment variable name and a boolean presence proof,
never the token value.

The following remain forbidden:

- direct issue scan from the local server;
- direct GitHub Project GraphQL scan;
- `workflow_dispatch` from the local scanner;
- POST, PATCH, PUT or DELETE GitHub mutation;
- SQL or Qdrant writes during the GitHub scan;
- storing user artifacts in the Autodoc development repository.

GitHub remains a review/workflow surface. The local server dataset remains the
operational copy and the local knowledge system remains authoritative.

## 0272-r1 clarification

The 0272-r1 wording that proposed a new issue-scan client is superseded. The
existing Actions artifact transport is the correct reusable path; the missing
piece was only a gated live composition of the already-started Project/Action,
fetch and dataset-sync surfaces.
