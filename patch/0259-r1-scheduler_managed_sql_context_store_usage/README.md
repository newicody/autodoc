# 0259-r1-scheduler_managed_sql_context_store_usage

Adapts Scheduler-managed SQLContextStore usage.  Scheduler does not start
PostgreSQL and no new SQL store is created.  Execution requires an existing
SQLContextStore object plus a policy decision id.

Apply:

```bash
python apply_patch_queue.py --patch 0259-r1-scheduler_managed_sql_context_store_usage --commit --push --allow-dirty
```

Dry-run smoke:

```bash
PYTHONPATH=src:. python tools/build_scheduler_managed_sql_context_store_usage_0259.py \
  --bootstrap .var/reports/scheduler_runtime_bootstrap_registry_attachment_0258.json \
  --output .var/reports/scheduler_managed_sql_context_store_usage_0259.json \
  --format summary
```

Execute smoke with smoke-only existing store:

```bash
PYTHONPATH=src:. python tools/build_scheduler_managed_sql_context_store_usage_0259.py \
  --bootstrap .var/reports/scheduler_runtime_bootstrap_registry_attachment_0258.json \
  --execute \
  --policy-decision-id policy:0259:demo \
  --demo-existing-store \
  --format summary
```
