# 0260-r9-record_adapter_typed_sql_context_ref_fix

Fixes the real `DbApiSqlContextStore` typed reference contract.

The execute smoke reached the real store and failed with:

```text
ValueError: context_ref must start with sql:
```

The adapter now normalises generated context references to `sql:<value>` while
preserving already-typed `sql:` references.

Apply:

```bash
python apply_patch_queue.py --patch 0260-r9-record_adapter_typed_sql_context_ref_fix --commit --push --allow-dirty
```
