# 0287-r7-r15-r2-r2-r3 — Python 3.14 dynamic tool import compatibility fix

This patch applies on the dirty tree left after applying:

- `0287-r7-r15-r2-r2-projects-views-actions-readiness-repair`;
- `0287-r7-r15-r2-r2-r1-projects-installation-budget-compatibility-fix`;
- `0287-r7-r15-r2-r2-r2-projects-installation-remaining-compatibility-markers-fix`.

It changes the dynamic tool test loader only.  The helper now registers the
module in `sys.modules` before `exec_module()`, matching Python's documented
programmatic import recipe and allowing dataclasses with postponed annotations
to load on Python 3.14.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r2-r3-python314-dynamic-tool-import-compatibility-fix \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r2-r3-python314-dynamic-tool-import-compatibility-fix \
  --commit \
  --push \
  --allow-dirty
```

Suggested commit message:

```text
fix Python 3.14 dynamic tool test imports
```
