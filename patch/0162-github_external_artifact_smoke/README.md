# 0162 — GitHub external artifact smoke

Apply:

```text
tar -xJf autodoc_patch_0162-github_external_artifact_smoke.tar.xz
python apply_patch_queue.py --patch 0162-github_external_artifact_smoke --dry-run --allow-dirty
python apply_patch_queue.py --patch 0162-github_external_artifact_smoke --commit --push --allow-dirty
```
