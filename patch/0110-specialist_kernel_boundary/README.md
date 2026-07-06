# 0110-specialist_kernel_boundary

Adds the specialist-to-kernel boundary: a typed `SpecialistKernelCommand` and boundary plan proving that specialist work enters through `Scheduler.emit()` and does not call `RouteRuntimeManager` directly.

Apply:

```bash
python apply_patch_queue.py --patch 0110-specialist_kernel_boundary --dry-run
python apply_patch_queue.py --patch 0110-specialist_kernel_boundary --commit --push
```

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_specialist_kernel_boundary.py
PYTHONPATH=src:. pytest -q tests/rules/test_specialist_kernel_boundary_0110_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
