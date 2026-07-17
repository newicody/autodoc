# 0241-r1-prod_server_ini_validation

Adds stdlib-only validation for the initial production server INI file. The
layout remains ConfigObj-compatible, while this phase avoids adding a new runtime
dependency.

Apply:

```bash
python apply_patch_queue.py --patch 0241-r1-prod_server_ini_validation --dry-run --allow-dirty
python apply_patch_queue.py --patch 0241-r1-prod_server_ini_validation --commit --push --allow-dirty
```
