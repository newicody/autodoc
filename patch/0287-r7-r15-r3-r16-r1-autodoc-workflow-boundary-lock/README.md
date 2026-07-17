# 0287-r7-r15-r3-r16-r1-autodoc-workflow-boundary-lock

This corrective patch assumes the obsolete root workflow is already absent
from the operator worktree. It adds only the boundary rule and documentation.

## Inspect the local deletion

```bash
git status --short -- .github/workflows
git ls-files --deleted -- .github/workflows
```

## Dry-run

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r16-r1-autodoc-workflow-boundary-lock \
  --dry-run \
  --allow-dirty
```

## Commit and push

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r16-r1-autodoc-workflow-boundary-lock \
  --commit \
  --push \
  --allow-dirty
```

The Patch Queue stages all changed non-`patch/` paths, including an existing
tracked deletion of the obsolete workflow.
