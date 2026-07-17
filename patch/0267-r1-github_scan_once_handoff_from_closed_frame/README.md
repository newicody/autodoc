# 0267-r1-github_scan_once_handoff_from_closed_frame

Adds a local GitHub scan-once handoff artifact from 0264 and 0266 reports.

Apply:

```bash
python apply_patch_queue.py --patch 0267-r1-github_scan_once_handoff_from_closed_frame --commit --push --allow-dirty
```

Smoke:

```bash
PYTHONPATH=src:. python tools/build_github_scan_once_handoff_0267.py \
  --closed-frame-report .var/reports/scheduler_managed_closed_result_frame_0264.json \
  --passive-report .var/reports/passive_supervisor_closed_result_frame_observation_0266.json \
  --repository newicody/autodoc \
  --output .var/reports/github_scan_once_handoff_0267.json \
  --format summary
```
