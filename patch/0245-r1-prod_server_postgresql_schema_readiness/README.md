# 0245-r1-prod_server_postgresql_schema_readiness

Adds PostgreSQL schema readiness from the production server INI. This phase emits
idempotent SQL text for review but does not connect to PostgreSQL or execute SQL.

Apply:

```bash
python apply_patch_queue.py --patch 0245-r1-prod_server_postgresql_schema_readiness --dry-run --allow-dirty
python apply_patch_queue.py --patch 0245-r1-prod_server_postgresql_schema_readiness --commit --push --allow-dirty
```
