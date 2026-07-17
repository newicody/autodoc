# 0255-r1-scheduler_owned_runtime_reuse_audit

Adds a read-only reuse audit before Scheduler-owned production execution code.

Apply:

```bash
python apply_patch_queue.py --patch 0255-r1-scheduler_owned_runtime_reuse_audit --commit --push --allow-dirty
```

Direct smoke:

```bash
PYTHONPATH=src:. python tools/audit_scheduler_owned_runtime_reuse_0255.py --format summary
```
