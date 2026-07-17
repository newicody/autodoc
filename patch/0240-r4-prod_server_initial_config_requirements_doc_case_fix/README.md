# 0240-r4-prod_server_initial_config_requirements_doc_case_fix

Fixes the exact lowercase rule string `publication review is required` in the
phase 0240 production server initial configuration documentation.

Apply after `0240-r3-prod_server_initial_config_requirements_doc_fix` if r3
failed during rule validation.

```bash
python apply_patch_queue.py --patch 0240-r4-prod_server_initial_config_requirements_doc_case_fix --dry-run --allow-dirty
python apply_patch_queue.py --patch 0240-r4-prod_server_initial_config_requirements_doc_case_fix --commit --push --allow-dirty
```
