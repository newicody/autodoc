# 0231-r1 scheduler EventBus supervisor source

Adds the first Scheduler upstream source helper for the existing passive supervisor sink.

Apply after `0230-r1-eventbus_passive_supervisor_sink`.

```bash
python apply_patch_queue.py --patch 0231-r1-scheduler_eventbus_supervisor_source --dry-run --allow-dirty
python apply_patch_queue.py --patch 0231-r1-scheduler_eventbus_supervisor_source --commit --push --allow-dirty
```
