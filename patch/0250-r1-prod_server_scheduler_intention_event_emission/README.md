# 0250-r1-prod_server_scheduler_intention_event_emission

Adds a read-only emission surface that derives immutable EventBus-shaped envelopes
from typed Scheduler intentions. This phase does not create EventBus or publish
events.

Apply:

```bash
python apply_patch_queue.py --patch 0250-r1-prod_server_scheduler_intention_event_emission --dry-run --allow-dirty
python apply_patch_queue.py --patch 0250-r1-prod_server_scheduler_intention_event_emission --commit --push --allow-dirty
```
