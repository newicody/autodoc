# 0268-r1-openrc_launcher_minimal_readiness

Adds readiness-only OpenRC launcher envelope after the closed prototype path.

Apply:

```bash
python apply_patch_queue.py --patch 0268-r1-openrc_launcher_minimal_readiness --commit --push --allow-dirty
```

Smoke:

```bash
PYTHONPATH=src:. python tools/build_openrc_launcher_minimal_readiness_0268.py \
  --closed-frame-report .var/reports/scheduler_managed_closed_result_frame_0264.json \
  --github-handoff .var/reports/github_scan_once_handoff_0267.json \
  --output .var/reports/openrc_launcher_minimal_readiness_0268.json \
  --script-output .var/reports/autodoc-local-runtime.openrc \
  --format summary
```
