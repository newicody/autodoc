# 0272-r2 — GitHub Actions artifact scan-once live binding

## Purpose

Close the already-started Project/Action artifact path without adding a direct
GitHub issue scanner or another GitHub transport.

The external repository workflow emits append-only GitHub Actions artifacts.
The local CLI validates the Project and server-fetch configurations, then reuses:

- `tools/run_github_actions_artifact_fetch_once.py` (0168) for bounded GET/download;
- `tools/run_github_artifact_server_sync_once.py` (0167) for the local raw/index/history/conversion-queue dataset.

The scan is plan-only by default. Live execution requires an explicit
`policy_decision_id`. The example fcron command contains a stable read-only
policy decision and the CLI accepts the existing 0165 `--config` calling
convention.

## Boundaries

- no direct issue API scan;
- no direct Project GraphQL scan;
- no `workflow_dispatch`;
- no POST, PATCH, PUT or DELETE GitHub mutation;
- token value read only by the existing 0168 IO boundary and never serialized;
- no SQL or Qdrant write;
- no Scheduler, SHM, RouteProxy or ControlProxy modification;
- no new external dependency, manager, orchestrator or polling loop.

The patch also removes the manual `workflow_dispatch` trigger from the workflow
template and replaces the obsolete configured scan command with the gated 0272
CLI.

## Required base

```text
740d1d36ea312f97b7f6db6684cfe7bca92f2d33
r1-github-real-read-only-scan-reuse-audit
```

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Offline plan smoke

```bash
PYTHONPATH=src:. python \
  tools/run_github_actions_artifact_scan_once_live_0272.py \
  --project-config config/github_project_push_frame.example.ini \
  --fetch-config config/github_artifact_server_fetch.example.ini \
  --output .var/reports/github_actions_artifact_scan_once_live_0272.json \
  --format summary
```

Expected plan properties:

```text
github_actions_artifact_scan_once_live_valid=True
execute=False
external_call_performed=False
direct_issue_scan_required=False
remote_mutation_allowed=False
```

## Live GET/download scan

The configured environment variable must contain a token able to read Actions
runs and artifacts from the allowed external repository.

```bash
export GITHUB_TOKEN='...'

PYTHONPATH=src:. python \
  tools/run_github_actions_artifact_scan_once_live_0272.py \
  --execute \
  --policy-decision-id policy:0272:actions-artifacts-read-only \
  --project-config config/github_project_push_frame.example.ini \
  --fetch-config config/github_artifact_server_fetch.example.ini \
  --max-runs 10 \
  --max-artifacts 20 \
  --output .var/reports/github_actions_artifact_scan_once_live_0272.json \
  --format summary
```

A successful live result keeps `remote_mutation_allowed=False` and reports the
number of downloaded, synchronized and already-skipped artifacts.
