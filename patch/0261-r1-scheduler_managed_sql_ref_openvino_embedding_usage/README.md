# 0261-r1-scheduler_managed_sql_ref_openvino_embedding_usage

Adds the 0261 usage path:

```text
sql_ref -> SQL rehydrate -> OpenVINO/E5 passage embedding
```

The patch only adds new files. It does not modify Scheduler.run, does not create
a RuntimeManager, and does not involve Qdrant.

Apply:

```bash
python apply_patch_queue.py --patch 0261-r1-scheduler_managed_sql_ref_openvino_embedding_usage --commit --push --allow-dirty
```

Dry-run smoke:

```bash
PYTHONPATH=src:. python tools/run_scheduler_managed_sql_ref_openvino_embedding_0261.py \
  --db-path .var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3 \
  --binding-report .var/reports/scheduler_managed_db_api_sql_context_store_binding_0260.json \
  --output .var/reports/scheduler_managed_sql_ref_openvino_embedding_0261.json \
  --format summary
```

Real OpenVINO execute smoke:

```bash
PYTHONPATH=src:. python tools/run_scheduler_managed_sql_ref_openvino_embedding_0261.py \
  --db-path .var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3 \
  --binding-report .var/reports/scheduler_managed_db_api_sql_context_store_binding_0260.json \
  --execute \
  --policy-decision-id policy:0261:demo \
  --format summary
```
