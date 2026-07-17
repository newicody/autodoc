# 0247-r2-prod_server_qdrant_collection_readiness_doc_fix

Fixes the phase 0247 architecture documentation so the rules test can find the
exact phrase `aligned with OpenVINO` on one line.

Apply after `0247-r1-prod_server_qdrant_collection_readiness` if r1 failed during
rule validation.

```bash
python apply_patch_queue.py --patch 0247-r2-prod_server_qdrant_collection_readiness_doc_fix --dry-run --allow-dirty
python apply_patch_queue.py --patch 0247-r2-prod_server_qdrant_collection_readiness_doc_fix --commit --push --allow-dirty
```
