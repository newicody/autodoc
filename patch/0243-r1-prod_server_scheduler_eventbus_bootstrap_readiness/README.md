# 0243-r1-prod_server_scheduler_eventbus_bootstrap_readiness

Adds Scheduler/EventBus bootstrap readiness checks using the validated production
server INI and 0242 component registry. This phase keeps factory references as
data and does not import or call factories.

Apply:

```bash
python apply_patch_queue.py --patch 0243-r1-prod_server_scheduler_eventbus_bootstrap_readiness --dry-run --allow-dirty
python apply_patch_queue.py --patch 0243-r1-prod_server_scheduler_eventbus_bootstrap_readiness --commit --push --allow-dirty
```
