# 0274-r5 — Existing-Scheduler fake laboratory closed-loop smoke

Composes r2, r3 and r4 using only injected existing runtime surfaces.

```bash
python apply_patch_queue.py \
  --patch 0274-r5-existing_scheduler_fake_laboratory_closed_loop_smoke \
  --dry-run \
  --allow-dirty
```

No Scheduler, queue, EventBus, registry or laboratory orchestrator is added.
