# 0287-r7-r15-r3-r7-r1-openvino-e5-async-rule-docstring-fix

This correction is designed for the current dirty worktree where the original
r7 patch was applied but tests stopped before commit.

It changes the runtime docstring and deliberately touches all eight r7 artifacts
so `apply_patch_queue.py` stages and commits the complete r7 unit.

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r7-r1-openvino-e5-async-rule-docstring-fix \
  --dry-run \
  --allow-dirty
```

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r7-r1-openvino-e5-async-rule-docstring-fix \
  --commit \
  --push \
  --allow-dirty
```
