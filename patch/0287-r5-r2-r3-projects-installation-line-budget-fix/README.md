# 0287-r5-r2-r3-projects-installation-line-budget-fix

Corrects the cumulative Projects installation line-budget assertion after the
compatibility markers restored by 0287-r5-r1 and 0287-r5-r2-r2.

```bash
python apply_patch_queue.py \
  --patch 0287-r5-r2-r3-projects-installation-line-budget-fix \
  --commit \
  --push \
  --allow-dirty
```
