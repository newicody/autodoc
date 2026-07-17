# 0263-r1-scheduler_managed_qdrant_recall_sql_rehydrate_usage

Adds the 0263 recall step:

```text
Qdrant recall -> sql_ref -> SQL rehydrate
```

Qdrant remains ref-only. SQL remains the durable content authority.

Apply:

```bash
python apply_patch_queue.py --patch 0263-r1-scheduler_managed_qdrant_recall_sql_rehydrate_usage --commit --push --allow-dirty
```
