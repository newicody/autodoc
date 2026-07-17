# 0260-r2-db_api_sql_context_store_binding_strict_candidate_import

Fixes the 0260 existing DbApiSqlContextStore binder.

The r1 binder selected helper classes such as DbApiSqlContextStoreBindingCandidate and imported temporary-root candidates through the normal Python module cache. r2 uses strict class matching and file-path loading for class-definition candidates.

Apply on top of the failed/applied 0260-r1 state:

```bash
python apply_patch_queue.py --patch 0260-r2-db_api_sql_context_store_binding_strict_candidate_import --commit --push --allow-dirty
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
