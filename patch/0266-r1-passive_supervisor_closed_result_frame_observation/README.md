# 0266-r1-passive_supervisor_closed_result_frame_observation

Adds PassiveSupervisor observation-only read model over 0265 EventBus facts.

Apply:

```bash
python apply_patch_queue.py --patch 0266-r1-passive_supervisor_closed_result_frame_observation --commit --push --allow-dirty
```

Smoke:

```bash
PYTHONPATH=src:. python tools/build_passive_supervisor_closed_result_frame_observation_0266.py \
  --observation-report .var/reports/closed_result_frame_eventbus_observation_0265.json \
  --output .var/reports/passive_supervisor_closed_result_frame_observation_0266.json \
  --format summary
```
