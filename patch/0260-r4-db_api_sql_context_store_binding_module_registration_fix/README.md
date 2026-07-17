# 0260-r4-db_api_sql_context_store_binding_module_registration_fix

Fixes the real helper `_load_module_from_candidate_path` added by 0260-r2.

The previous 0260-r3 patch targeted the wrong synthetic shape.  This patch uses
the real context:

```python
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
return module
```

and registers the dynamically loaded module in `sys.modules` before
`exec_module`, which is required by dataclasses/decorators that inspect
`sys.modules[__module__]`.

Apply on top of the current failed 0260 state:

```bash
python apply_patch_queue.py --patch 0260-r4-db_api_sql_context_store_binding_module_registration_fix --commit --push --allow-dirty
```
