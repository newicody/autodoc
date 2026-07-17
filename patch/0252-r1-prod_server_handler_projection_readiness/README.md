# 0252-r1-prod_server_handler_projection_readiness

Adds handler projection readiness that derives a future Qdrant projection request
from the SQL controlled write handler frame. This phase does not run OpenVINO or
write Qdrant points.

Apply:

```bash
python apply_patch_queue.py --patch 0252-r1-prod_server_handler_projection_readiness --dry-run --allow-dirty
python apply_patch_queue.py --patch 0252-r1-prod_server_handler_projection_readiness --commit --push --allow-dirty
```
