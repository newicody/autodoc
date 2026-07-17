# 0284-r9-r1 — specialists/laboratories rule compatibility fix

Apply this patch **after** the failed `0284-r9` queue run. The r9 files are
already present in the working tree because `git apply` succeeded before the
rule suite stopped the commit.

The patch fixes only the three reported architecture-rule regressions:

- restores the 0282 architecture-view links in `doc/README_CURRENT.md`;
- restores the stable 0281 artifact and milestone markers;
- makes the `0284-r1-r5` installation rule validate cumulative history rather
  than freezing the current guide version.

`templates/github/projects-repository/INSTALLATION.md` remains unchanged at
version `0284-r9`.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0284-r9-r1-specialists-laboratories-rule-compatibility-fix \
  --commit \
  --push \
  --allow-dirty
```

Do not reapply `0284-r9` first.

## Validation performed while packaging

```text
git apply --check: OK
git diff --check: OK
focused compatibility rules: 7 passed
compileall focused tests: OK
```
