# 0235-r2-patch_queue_ignored_runtime_artifacts_guard

Fixes patch queue commit selection so ignored `.var/` runtime artifacts are
not passed to `git add`.

Apply:

```bash
python apply_patch_queue.py --patch 0235-r2-patch_queue_ignored_runtime_artifacts_guard --dry-run --allow-dirty
python apply_patch_queue.py --patch 0235-r2-patch_queue_ignored_runtime_artifacts_guard --commit --push --allow-dirty
```
