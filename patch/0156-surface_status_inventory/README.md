# 0156 — surface status inventory

Safe-apply variant.

This patch intentionally avoids modifying `00_global.dot` because the local graph
has drifted and a context hunk failed at line 13. The canonical graph refresh
should be done in a follow-up patch generated against the exact local file.

Apply:

```bash
python apply_patch_queue.py --patch 0156-surface_status_inventory --dry-run
python apply_patch_queue.py --patch 0156-surface_status_inventory --commit --push --allow-dirty
```

The patch queue cleaner removes untracked generated `.svg` files before and after
application. If `.svg` files are tracked, the cleaner blocks and they must be
removed from Git explicitly.
