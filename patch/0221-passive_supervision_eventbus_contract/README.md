# 0221 — Passive supervision EventBus contract

This patch locks the written architecture/rule direction for passive supervision before any further functional patch.

It is intentionally documentation/rule only:

- EventBus is the canonical transport.
- Scheduler remains upstream authority.
- PassiveSupervisorSink is downstream-only.
- snapshots and events.jsonl are optional outputs, not runtime backbone.
- no runtime code is changed.

Apply with:

```bash
python apply_patch_queue.py --patch 0221-passive_supervision_eventbus_contract --dry-run --allow-dirty
python apply_patch_queue.py --patch 0221-passive_supervision_eventbus_contract --commit --push --allow-dirty
```
