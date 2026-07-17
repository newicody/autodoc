# 0251-r1-prod_server_sql_controlled_write_handler_readiness

Adds a dry-run SQL controlled write handler frame derived from the Scheduler
intention event surface and PostgreSQL schema readiness. This phase does not
connect to PostgreSQL or execute SQL.

Apply:

```bash
python apply_patch_queue.py --patch 0251-r1-prod_server_sql_controlled_write_handler_readiness --dry-run --allow-dirty
python apply_patch_queue.py --patch 0251-r1-prod_server_sql_controlled_write_handler_readiness --commit --push --allow-dirty
```
