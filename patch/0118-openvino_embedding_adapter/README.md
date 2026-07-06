# 0118 — OpenVINOEmbeddingAdapter

This patch adds the embedding adapter boundary after SQL hydration.

It introduces immutable embedding target, policy, text, vector, and batch structures. The adapter consumes `SqlHydratedContextBundle`, builds bounded E5-style texts, calls an injected executor, validates normalized vectors, and returns a serializable batch for a later Qdrant projection adapter.

The adapter does not import the OpenVINO package directly. The real OpenVINO import remains isolated in `src/inference/openvino_runtime.py`.

## Apply

```bash
python apply_patch_queue.py --patch 0118-openvino_embedding_adapter --dry-run
python apply_patch_queue.py --patch 0118-openvino_embedding_adapter --commit --push
```

## Validate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_openvino_embedding_adapter.py
PYTHONPATH=src:. pytest -q tests/rules/test_openvino_embedding_adapter_0118_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
