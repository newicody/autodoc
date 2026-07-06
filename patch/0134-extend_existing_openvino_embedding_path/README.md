# 0134 — Extend existing OpenVINO/E5 embedding path

This patch does not create a new OpenVINO or E5 adapter.

It adds tests and documentation that lock the existing inference surfaces as the supported path:

- `src/inference/openvino_embedding_adapter.py`
- `src/inference/openvino_runtime.py`
- `src/inference/openvino_backend.py`
- `src/inference/e5_pipeline.py`
- `src/inference/embedding_pipeline.py`
- `src/inference/registry.py`

It also adds a code-rule addendum requiring future OpenVINO/E5 work to reuse or extend those surfaces unless a documented gap proves otherwise.

## Validation

Run on the full repository:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/inference/test_openvino_embedding_existing_path_0134.py tests/rules/test_openvino_existing_embedding_path_0134_rule.py
PYTHONPATH=src:. pytest -q tests/inference tests/rules
```
