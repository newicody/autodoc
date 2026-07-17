# 0287-r7-r15-r3-r12-love-specialist-live-projection-binding

## Dry-run

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r12-love-specialist-live-projection-binding \
  --dry-run \
  --allow-dirty
```

## Commit and push

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r12-love-specialist-live-projection-binding \
  --commit \
  --push \
  --allow-dirty
```

This unit is additive. It binds the two existing Scheduler-produced love
specialist analyses to SQL authority and the injected live E5/Qdrant projector.
Hybrid recall and liaison synthesis remain the next unit.
