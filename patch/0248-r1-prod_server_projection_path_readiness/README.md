# 0248-r1-prod_server_projection_path_readiness

Adds production projection path readiness that composes PostgreSQL, OpenVINO, and
Qdrant readiness into a future Qdrant point shape. The patch remains read-only and
does not run inference or call Qdrant.

Apply:

```bash
python apply_patch_queue.py --patch 0248-r1-prod_server_projection_path_readiness --dry-run --allow-dirty
python apply_patch_queue.py --patch 0248-r1-prod_server_projection_path_readiness --commit --push --allow-dirty
```
