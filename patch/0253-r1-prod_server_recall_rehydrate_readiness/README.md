# 0253-r1-prod_server_recall_rehydrate_readiness

Adds readiness-only Qdrant recall payload to PostgreSQL rehydrate read shape.

Apply:

```bash
python apply_patch_queue.py --patch 0253-r1-prod_server_recall_rehydrate_readiness --dry-run --allow-dirty
python apply_patch_queue.py --patch 0253-r1-prod_server_recall_rehydrate_readiness --commit --push --allow-dirty
```

Smoke:

```bash
PYTHONPATH=src:. python tools/run_prod_server_recall_rehydrate_readiness_0253.py --check-only --format summary
```
