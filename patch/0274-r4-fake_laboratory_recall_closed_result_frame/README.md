# 0274-r4 — Fake laboratory recall closed ResultFrame

Reuses 0261, 0263, 0264, 0265 and 0266 to recall and verify the durable
laboratory output, then build passive observation and visual models.

```bash
python apply_patch_queue.py \
  --patch 0274-r4-fake_laboratory_recall_closed_result_frame \
  --dry-run \
  --allow-dirty
```

No Scheduler, SQL write, Qdrant write or GitHub mutation is added.
