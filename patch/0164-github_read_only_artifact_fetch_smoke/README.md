# 0164 — GitHub read-only artifact fetch smoke

Apply:

```text
tar -xJf autodoc_patch_0164-github_read_only_artifact_fetch_smoke.tar.xz
python apply_patch_queue.py --patch 0164-github_read_only_artifact_fetch_smoke --dry-run --allow-dirty
python apply_patch_queue.py --patch 0164-github_read_only_artifact_fetch_smoke --commit --push --allow-dirty
```
