# 0287-r5-r2-projects-view-owner-endpoint-and-guide-compatibility

Corrects the user-owned ProjectV2 view endpoint and restores the final
cumulative installation markers.

```bash
python apply_patch_queue.py \
  --patch 0287-r5-r2-projects-view-owner-endpoint-and-guide-compatibility \
  --commit \
  --push \
  --allow-dirty
```

After application, copy the corrected reconciler into `newicody/projects` and
generate a new preview/digest before execution.
