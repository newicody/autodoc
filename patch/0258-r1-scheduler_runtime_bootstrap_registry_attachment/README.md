# 0258-r1-scheduler_runtime_bootstrap_registry_attachment

Attaches the 0257 Scheduler-owned runtime registry metadata to Scheduler
bootstrap.  It does not create a RuntimeManager, instantiate components, or
modify Scheduler.run.

Apply:

```bash
python apply_patch_queue.py --patch 0258-r1-scheduler_runtime_bootstrap_registry_attachment --commit --push --allow-dirty
```

Direct smoke:

```bash
PYTHONPATH=src:. python tools/build_scheduler_runtime_bootstrap_registry_attachment_0258.py \
  --registry .var/reports/scheduler_owned_runtime_registry_0257.json \
  --output .var/reports/scheduler_runtime_bootstrap_registry_attachment_0258.json \
  --format summary
```
