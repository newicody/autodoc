# 0272-r4 — GitHub ProjectV2 snapshot change detection

## Required base

The patch requires `0272-r3-github_project_v2_query_only_snapshot` to be present.
It only adds new files and does not modify the r3 GraphQL reader.

## Purpose

Compare immutable local ProjectV2 snapshots without contacting GitHub. A single
snapshot produces a valid baseline. Later snapshots produce immutable,
content-addressed change sets describing added, removed, changed and unchanged
items, Status transitions and Project field-definition changes.

## Reuse decision

The implementation imports and validates the existing r3 `SNAPSHOT_SCHEMA`.
No second GraphQL client, Project reader, manager or orchestrator is created.
No non-stdlib dependency is added.

## Apply

```bash
tar -xJf /mnt/data/0272-r4-github_project_v2_snapshot_change_detection.tar.xz
python apply_patch_queue.py \
  --patch 0272-r4-github_project_v2_snapshot_change_detection \
  --dry-run \
  --allow-dirty
python apply_patch_queue.py \
  --patch 0272-r4-github_project_v2_snapshot_change_detection \
  --commit \
  --push \
  --allow-dirty
```

## Validate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## First baseline

```bash
PYTHONPATH=src:. python \
  tools/detect_github_project_v2_snapshot_changes_0272.py \
  --execute \
  --policy-decision-id policy:0272:project-v2-change-baseline \
  --format summary
```

## Later comparisons

Run the r3 snapshot again after Project changes, then rerun the same r4 command.
The newest two distinct content-addressed snapshots will be compared locally.

## Next phases

- 0272-r5: convert relevant change-set entries into typed local handoffs;
- 0272-r6: gate accepted handoffs into the existing SQL authority path;
- 0272-r7: compose Project snapshot → change detection → local handoff;
- 0273: separate, explicit remote Project mutation gate;
- operational pass: fcron/OpenRC scheduling, rate-limit/error hardening, backups and round-trip smoke.
