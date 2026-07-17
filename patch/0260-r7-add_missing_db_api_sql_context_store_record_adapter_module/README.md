# 0260-r7-add_missing_db_api_sql_context_store_record_adapter_module

Adds the missing adapter module imported by 0260-r6 and stages the r6 binding
file through a tiny boundary marker.

Apply on top of the current failed 0260-r6 state:

```bash
python apply_patch_queue.py --patch 0260-r7-add_missing_db_api_sql_context_store_record_adapter_module --commit --push --allow-dirty
```
