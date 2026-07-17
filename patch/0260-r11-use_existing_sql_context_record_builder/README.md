# 0260-r11-use_existing_sql_context_record_builder

Uses the existing `build_sql_context_record` helper from `context.sql_context_store`
instead of passing a SimpleNamespace to `DbApiSqlContextStore.upsert_record`.

Apply:

```bash
python apply_patch_queue.py --patch 0260-r11-use_existing_sql_context_record_builder --commit --push --allow-dirty
```
