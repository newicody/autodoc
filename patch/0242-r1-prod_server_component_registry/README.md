# 0242-r1-prod_server_component_registry

Adds a declarative production server component registry built from the validated
INI introduced by `0241-r1-prod_server_ini_validation`. The registry validates
factory reference syntax and computes dependency order without importing or
calling factories.

Apply:

```bash
python apply_patch_queue.py --patch 0242-r1-prod_server_component_registry --dry-run --allow-dirty
python apply_patch_queue.py --patch 0242-r1-prod_server_component_registry --commit --push --allow-dirty
```
