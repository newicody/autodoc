# 0238-r1-passive_supervisor_visual_pipeline_smoke

Adds a local read-only pipeline smoke tool that composes existing reports:

```text
0234 -> 0236 -> 0237
```

Apply:

```bash
python apply_patch_queue.py --patch 0238-r1-passive_supervisor_visual_pipeline_smoke --dry-run --allow-dirty
python apply_patch_queue.py --patch 0238-r1-passive_supervisor_visual_pipeline_smoke --commit --push --allow-dirty
```
