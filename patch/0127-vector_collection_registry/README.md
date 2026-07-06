# 0127 — Vector collection registry

Adds a local/importable vector collection registry contract.

This patch turns the 0126 role-oriented collection plan into a registry and ensure plan that a future Qdrant adapter can execute. It does not import or call Qdrant, OpenVINO, PostgreSQL, GitHub, HTTP, sockets, Graphviz, NetworkX, or VisPy.

Apply:

```bash
python apply_patch_queue.py --patch 0127-vector_collection_registry --dry-run
python apply_patch_queue.py --patch 0127-vector_collection_registry --commit --push
```

Validate:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_vector_collection_registry.py
PYTHONPATH=src:. pytest -q tests/rules/test_vector_collection_registry_0127_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
