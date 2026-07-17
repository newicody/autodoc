# 0287-r7-r15-r3-r16-r3-correlated-fetched-actions-run-readiness

Cette unité étend le fetch 0168/0272 existant. Elle ne crée ni second poller,
ni second downloader.

## Dry-run

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r16-r3-correlated-fetched-actions-run-readiness \
  --dry-run \
  --allow-dirty
```

## Commit et push

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r16-r3-correlated-fetched-actions-run-readiness \
  --commit \
  --push \
  --allow-dirty
```

## Scan de disponibilité après intégration

```bash
python tools/run_github_actions_artifact_scan_once_live_0272.py \
  --project-config config/github_project_push_frame.example.ini \
  --fetch-config config/github_artifact_server_fetch.example.ini \
  --execute \
  --policy-decision-id policy:projects-artifact-fetch-r16-r3 \
  --max-runs 10 \
  --max-artifacts 30 \
  --format json |
tee /tmp/github-actions-artifact-ready-runs.json
```

Inspection :

```bash
jq '{valid, counts, ready_runs, deferred_runs, boundaries}' \
  /tmp/github-actions-artifact-ready-runs.json
```
