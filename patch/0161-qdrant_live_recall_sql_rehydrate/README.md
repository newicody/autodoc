# 0161 — Qdrant live recall SQL rehydrate

Apply:

```bash
tar -xJf autodoc_patch_0161-qdrant_live_recall_sql_rehydrate.tar.xz
python apply_patch_queue.py --patch 0161-qdrant_live_recall_sql_rehydrate --dry-run --allow-dirty
python apply_patch_queue.py --patch 0161-qdrant_live_recall_sql_rehydrate --commit --push --allow-dirty
```
