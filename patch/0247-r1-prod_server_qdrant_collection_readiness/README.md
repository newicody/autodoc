# 0247-r1-prod_server_qdrant_collection_readiness

Adds Qdrant collection readiness aligned with the OpenVINO embedding readiness
from 0246. The patch checks dimension, distance, normalized-vector expectation,
and mandatory payload fields without calling Qdrant.

Apply:

```bash
python apply_patch_queue.py --patch 0247-r1-prod_server_qdrant_collection_readiness --dry-run --allow-dirty
python apply_patch_queue.py --patch 0247-r1-prod_server_qdrant_collection_readiness --commit --push --allow-dirty
```
