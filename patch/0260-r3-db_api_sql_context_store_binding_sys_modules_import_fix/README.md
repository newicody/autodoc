# 0260-r3-db_api_sql_context_store_binding_sys_modules_import_fix

Fixes file-path imports for the existing `DbApiSqlContextStore` binding.

The r2 binder selects the correct class-definition candidate but can fail during
`exec_module` with:

```text
'NoneType' object has no attribute '__dict__'
```

That happens when decorators/dataclasses inspect `sys.modules[__module__]`
before the dynamically loaded module is registered.  This patch inserts the
module into `sys.modules` before `exec_module`, and removes it again on import
failure.

Apply on top of 0260-r2:

```bash
python apply_patch_queue.py --patch 0260-r3-db_api_sql_context_store_binding_sys_modules_import_fix --commit --push --allow-dirty
```
