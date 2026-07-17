# 0287-r7-r8-r6 — authorized context-impact execution

This patch applies an explicitly authorized r8-r5 context-impact plan through
existing Scheduler, Dispatcher/EventBus and route-adapter boundaries.

## Prerequisite

- `0287-r7-r8-r5-context-revision-task-impact-policy`

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r8-r6-authorized-context-impact-execution \
  --dry-run \
  --allow-dirty
```

After a green dry-run:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r8-r6-authorized-context-impact-execution \
  --commit \
  --push \
  --allow-dirty
```

## Boundaries

- Scheduler remains the only orchestration authority.
- SQL remains the semantic-context authority.
- EventBus remains observation-only.
- ControlProxy is used only through the existing route adapter and only for an
  explicit transport transition.
- No Qdrant, OpenVINO, GitHub or ProjectV2 mutation is added.
- `INSTALLATION.md` was reviewed and is unchanged.
