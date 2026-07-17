# 0240-r3-prod_server_initial_config_requirements_doc_fix

Fixes the phase 0240 production server initial configuration documentation so the
rules test can find the exact sentence `Copilot output is advisory only.` on one line.

Apply after `0240-r2-prod_server_initial_config_requirements` if r2 failed during
rule validation.

```bash
python apply_patch_queue.py --patch 0240-r3-prod_server_initial_config_requirements_doc_fix --dry-run --allow-dirty
python apply_patch_queue.py --patch 0240-r3-prod_server_initial_config_requirements_doc_fix --commit --push --allow-dirty
```
