# 0256-r1-scheduler_owned_runtime_reuse_source_map

Builds a filtered source map from the 0255 reuse audit.  This is the last audit
before adapting existing runtime surfaces under Scheduler ownership.

Apply:

```bash
python apply_patch_queue.py --patch 0256-r1-scheduler_owned_runtime_reuse_source_map --commit --push --allow-dirty
```

Direct smoke:

```bash
PYTHONPATH=src:. python tools/build_scheduler_owned_runtime_reuse_source_map_0256.py --output .var/reports/scheduler_owned_runtime_reuse_source_map_0256.json --format summary
```
