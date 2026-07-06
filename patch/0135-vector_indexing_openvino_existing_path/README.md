# 0135 — vector indexing through existing OpenVINO path

Tests/docs phase proving `VectorEmbeddingJob` can feed the existing OpenVINO/E5 embedding contracts without a parallel adapter.

Apply after 0134 is committed.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/inference/test_vector_indexing_openvino_existing_path_0135.py tests/rules/test_vector_indexing_openvino_existing_path_0135_rule.py
PYTHONPATH=src:. pytest -q tests/inference tests/rules
```
