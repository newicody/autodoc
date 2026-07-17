# 0246-r1-prod_server_openvino_embedding_readiness

Adds explicit OpenVINO embedding readiness for multilingual-e5-small. This phase
locks model id, tokenizer, device candidates, dimension, normalization, pooling,
Qdrant distance, and E5 query/passage prefixes without importing OpenVINO or
loading a model.

Apply:

```bash
python apply_patch_queue.py --patch 0246-r1-prod_server_openvino_embedding_readiness --dry-run --allow-dirty
python apply_patch_queue.py --patch 0246-r1-prod_server_openvino_embedding_readiness --commit --push --allow-dirty
```
