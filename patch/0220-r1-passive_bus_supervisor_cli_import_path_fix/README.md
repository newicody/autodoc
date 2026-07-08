# 0220-r1 - Passive Bus Supervisor CLI Import Path Fix

This is a small follow-up fix for `0220-passive_bus_supervisor_cellular_snapshot`.

The original `0220` patch applies and passes rule tests, but the full suite
reveals that direct subprocess execution of:

```bash
python tools/run_passive_bus_supervisor_cellular_snapshot_0220.py
```

can fail because Python places `tools/` on `sys.path`, not necessarily the
repository root. The CLI imports `src.context...`, so it must insert the repo
root before importing project modules.

This patch:

- adds `sys.path` root setup to the CLI
- updates the 0220 changelog
- updates the 0220 phase test report

It does not change the passive authority boundary.

## Apply

Apply this after `0220` has already been applied and left in the worktree:

```bash
python apply_patch_queue.py \
  --patch 0220-r1-passive_bus_supervisor_cli_import_path_fix \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0220-r1-passive_bus_supervisor_cli_import_path_fix \
  --commit \
  --push \
  --allow-dirty
```

