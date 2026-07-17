# 0287-r7-r15-r3-r16-r2-r1-installation-budget-runbook-split

Incremental correction after r16-r2 was applied and the rules suite failed.

```bash
python apply_patch_queue.py --patch 0287-r7-r15-r3-r16-r2-r1-installation-budget-runbook-split --dry-run --allow-dirty
python apply_patch_queue.py --patch 0287-r7-r15-r3-r16-r2-r1-installation-budget-runbook-split --commit --push --allow-dirty
```

The commit includes both the previously applied r16-r2 changes and this correction.
