# Changelog — Phase 6.4 Patch Queue Status

## Goal

Add a read-only status/preflight command to `apply_patch_queue.py` so an operator can answer “where is the repository now?” before applying the next patch.

## Added

- `python apply_patch_queue.py --status`
- `python apply_patch_queue.py --status --status-format json`
- A stable JSON schema: `missipy.patch_queue.status.v1`
- Detection of versioned patch directories and forbidden flat patch files.
- Reporting of dirty worktree lines, tracked generated artifacts and local generated artifacts.
- Redacted SSH configuration status: the command reports whether SSH/cert/local config are configured but never prints key or certificate paths.

## Not added

- No business logic.
- No Scheduler modification.
- No GitHub API.
- No network call in status mode.
- No external dependency.
