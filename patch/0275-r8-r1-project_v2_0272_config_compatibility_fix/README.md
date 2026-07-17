# 0275-r8-r1-project_v2_0272_config_compatibility_fix

Restore the locked 0272 configuration sections while preserving the new
isolated `[workflow_dispatch]` section from 0275-r8.

```bash
python apply_patch_queue.py \
  --patch 0275-r8-r1-project_v2_0272_config_compatibility_fix \
  --dry-run \
  --allow-dirty
```
