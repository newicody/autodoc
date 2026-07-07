# 0159 — Qdrant recall SQL rehydrate

Adds `tools/run_qdrant_recall_sql_rehydrate_smoke.py`.

```bash
tar -xJf autodoc_patch_0159-qdrant_recall_sql_rehydrate.tar.xz
python apply_patch_queue.py --patch 0159-qdrant_recall_sql_rehydrate --dry-run --allow-dirty
python apply_patch_queue.py --patch 0159-qdrant_recall_sql_rehydrate --commit --push --allow-dirty
```
