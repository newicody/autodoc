# 0254-r2-scheduler_owned_runtime_component_lifecycle

Pivots the production runtime model toward Scheduler-owned runtime components.

Apply:

```bash
python apply_patch_queue.py --patch 0254-r2-scheduler_owned_runtime_component_lifecycle --commit --push --allow-dirty
```

Direct smoke:

```bash
PYTHONPATH=src:. python tools/run_scheduler_owned_runtime_component_lifecycle_0254.py --format summary
```
