# 0281-r4-pinned-cached-copilot-cli-runtime

```text
autodoc: change required
projects: change required
projects_repository_change_required: true
```

Apply to Autodoc:

```bash
python apply_patch_queue.py \
  --patch 0281-r4-pinned-cached-copilot-cli-runtime \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0281-r4-pinned-cached-copilot-cli-runtime \
  --commit \
  --push \
  --allow-dirty
```

Deploy to `newicody/projects` by following:

```text
patch/0281-r4-pinned-cached-copilot-cli-runtime/projects-deployment/DEPLOY.md
```
