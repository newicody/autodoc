# 0257-r1-scheduler_owned_runtime_registry_from_reuse_map

Builds a Scheduler-owned runtime registry from the 0256 reuse source map.
No component is instantiated and no RuntimeManager is created.

Apply:

```bash
python apply_patch_queue.py --patch 0257-r1-scheduler_owned_runtime_registry_from_reuse_map --commit --push --allow-dirty
```

Direct smoke:

```bash
PYTHONPATH=src:. python tools/build_scheduler_owned_runtime_registry_0257.py \
  --source-map .var/reports/scheduler_owned_runtime_reuse_source_map_0256.json \
  --output .var/reports/scheduler_owned_runtime_registry_0257.json \
  --format summary
```
