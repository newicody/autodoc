# Phase 6.4 — Patch Queue Status

This phase adds a read-only preflight command to the local patch queue tool:

```bash
python apply_patch_queue.py --status
python apply_patch_queue.py --status --status-format json
```

The command is intended to be run before applying a patch so the operator can see the current branch, HEAD, dirty worktree, available patch directories, forbidden flat patches, tracked generated artifacts and redacted SSH configuration status.

It performs no network call and applies no patch.
