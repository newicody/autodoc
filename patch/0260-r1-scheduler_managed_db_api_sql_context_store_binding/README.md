# 0260-r1-scheduler_managed_db_api_sql_context_store_binding

Binds the existing DbApiSqlContextStore to Scheduler-managed SQL usage, replacing
the 0259 demo store without creating a new SQL store.

Apply:

```bash
python apply_patch_queue.py --patch 0260-r1-scheduler_managed_db_api_sql_context_store_binding --commit --push --allow-dirty
```

Discovery smoke:

```bash
PYTHONPATH=src:. python tools/bind_scheduler_managed_db_api_sql_context_store_0260.py \
  --bootstrap .var/reports/scheduler_runtime_bootstrap_registry_attachment_0258.json \
  --output .var/reports/scheduler_managed_db_api_sql_context_store_binding_0260.json \
  --format summary
```

Execute smoke:

```bash
PYTHONPATH=src:. python tools/bind_scheduler_managed_db_api_sql_context_store_0260.py \
  --bootstrap .var/reports/scheduler_runtime_bootstrap_registry_attachment_0258.json \
  --execute \
  --policy-decision-id policy:0260:demo \
  --db-path .var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3 \
  --format summary
```
