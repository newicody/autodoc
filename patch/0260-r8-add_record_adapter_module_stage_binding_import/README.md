# 0260-r8-add_record_adapter_module_stage_binding_import

Adds the missing adapter module imported by 0260-r6 and stages the r6 binding
file through a constant inserted immediately after the r6 adapter import.

Apply on top of the current failed 0260-r6 state:

```bash
python apply_patch_queue.py --patch 0260-r8-add_record_adapter_module_stage_binding_import --commit --push --allow-dirty
```
