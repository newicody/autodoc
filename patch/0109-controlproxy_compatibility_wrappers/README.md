# 0109-controlproxy_compatibility_wrappers

Marks old ControlProxy Scheduler-facing helpers as compatibility wrappers and locks the replacement path as `Handler -> RouteRuntimeManager`.

Apply:

```bash
python apply_patch_queue.py --patch 0109-controlproxy_compatibility_wrappers --dry-run
python apply_patch_queue.py --patch 0109-controlproxy_compatibility_wrappers --commit --push
```

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_controlproxy_compatibility_wrappers.py
PYTHONPATH=src:. pytest -q tests/rules/test_controlproxy_compatibility_wrappers_0109_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
