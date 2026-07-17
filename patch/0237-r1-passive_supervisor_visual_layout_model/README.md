# 0237-r1-passive_supervisor_visual_layout_model

Adds a read-only deterministic visual layout model derived from passive
supervisor snapshots/read-models. No renderer or non-stdlib dependency is added.

Apply:

```bash
python apply_patch_queue.py --patch 0237-r1-passive_supervisor_visual_layout_model --dry-run --allow-dirty
python apply_patch_queue.py --patch 0237-r1-passive_supervisor_visual_layout_model --commit --push --allow-dirty
```
