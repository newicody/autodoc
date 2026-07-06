# 0111-route_dev_shm_runtime_boundary

Adds an explicit `/dev/shm` runtime root boundary for route mmap/eventfd data plane placement.

Apply from repository root:

```bash
unzip -o /mnt/data/0111-route_dev_shm_runtime_boundary.zip -d .
python apply_patch_queue.py --patch 0111-route_dev_shm_runtime_boundary --dry-run
python apply_patch_queue.py --patch 0111-route_dev_shm_runtime_boundary --commit --push
```

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_route_dev_shm_runtime.py
PYTHONPATH=src:. pytest -q tests/rules/test_route_dev_shm_runtime_0111_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
