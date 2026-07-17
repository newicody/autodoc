# 0281-r3-fetch-once-run-group-integration

## Purpose

Reuse the existing 0168 `--sync-tool` port to compose:

```text
0168 Actions fetch
-> existing 0167 raw sync
-> 0281-r2 run assembly
-> 0275 intake
-> stable local run-group report
```

## Repository impact

```text
autodoc: change required
projects: no change required
projects_repository_change_required: false
```

A local command/service configuration change is required:

```text
--sync-tool tools/run_github_dual_artifact_server_sync_once_0281.py
```

## Apply

```bash
python apply_patch_queue.py \
  --patch 0281-r3-fetch-once-run-group-integration \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0281-r3-fetch-once-run-group-integration \
  --commit \
  --push \
  --allow-dirty
```

## Focused tests

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/tools/test_github_dual_artifact_server_sync_once_0281.py \
  tests/rules/test_github_dual_artifact_fetch_run_group_integration_0281_rule.py
```

## Next repository impact

`0281-r4-pinned-cached-copilot-cli-runtime` will require changes in both
`autodoc` templates and the deployed `newicody/projects` workflow/policy.
