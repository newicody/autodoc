# 0264-r1-scheduler_managed_closed_result_frame

Adds the non-runtime closed ResultFrame composer for the 0260-0263 path.

Apply:

```bash
python apply_patch_queue.py --patch 0264-r1-scheduler_managed_closed_result_frame --commit --push --allow-dirty
```

Smoke:

```bash
PYTHONPATH=src:. python tools/compose_scheduler_managed_closed_result_frame_0264.py \
  --sql-write-report .var/reports/scheduler_managed_db_api_sql_context_store_binding_0260.json \
  --embedding-report .var/reports/scheduler_managed_sql_ref_openvino_embedding_0261.json \
  --projection-report .var/reports/scheduler_managed_embedding_qdrant_projection_0262.json \
  --recall-rehydrate-report .var/reports/scheduler_managed_qdrant_recall_sql_rehydrate_0263.json \
  --output .var/reports/scheduler_managed_closed_result_frame_0264.json \
  --format summary
```
