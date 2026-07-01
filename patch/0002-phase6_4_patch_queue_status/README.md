# 0002 — Phase 6.4 Patch Queue Status

This patch adds a read-only status/preflight command to `apply_patch_queue.py`.

## Apply

Copy this directory into the repository under `patch/`, then run:

```bash
python apply_patch_queue.py --patch 0002-phase6_4_patch_queue_status --dry-run
python apply_patch_queue.py --patch 0002-phase6_4_patch_queue_status
```

## New commands

```bash
python apply_patch_queue.py --status
python apply_patch_queue.py --status --status-format json
```

The status command reports branch, HEAD, dirty worktree, available patch directories, forbidden flat patches, tracked generated artifacts, local generated artifacts, remote URL and redacted SSH configuration state.

It does not apply a patch, run tests, fetch, push, or reveal SSH key/certificate paths.

## Gate after apply

```bash
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src pytest -q tests/test_apply_patch_queue_status.py
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```
