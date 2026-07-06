# 0099-architecture_graph_inventory

Architecture graph inventory and root-attached runtime overlay for the
ControlProxy / ControlFS / mmap route path.

Apply:

```bash
python apply_patch_queue.py --patch 0099-architecture_graph_inventory --dry-run
python apply_patch_queue.py --patch 0099-architecture_graph_inventory --commit --push
```

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/rules/test_architecture_graph_inventory_0099_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
