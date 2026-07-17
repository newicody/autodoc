# 0265-r1-closed_result_frame_eventbus_observation

Adds EventBus observation-only facts for the 0264 closed ResultFrame.

Apply:

```bash
python apply_patch_queue.py --patch 0265-r1-closed_result_frame_eventbus_observation --commit --push --allow-dirty
```

Smoke:

```bash
PYTHONPATH=src:. python tools/build_closed_result_frame_eventbus_observation_0265.py \
  --frame-report .var/reports/scheduler_managed_closed_result_frame_0264.json \
  --output .var/reports/closed_result_frame_eventbus_observation_0265.json \
  --publish-demo \
  --format summary
```
