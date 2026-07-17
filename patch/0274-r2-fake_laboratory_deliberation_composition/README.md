# 0274-r2 — Fake laboratory deliberation composition

Composes the existing Scheduler visit path, deliberation contracts, liaison
synthesis and local final artifact.

```bash
python apply_patch_queue.py \
  --patch 0274-r2-fake_laboratory_deliberation_composition \
  --dry-run \
  --allow-dirty
```

No Scheduler, queue, EventBus, registry or external backend is added.
