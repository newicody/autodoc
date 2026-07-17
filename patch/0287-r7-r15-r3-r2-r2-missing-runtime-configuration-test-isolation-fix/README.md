# 0287-r7-r15-r3-r2-r2 — missing runtime configuration test isolation fix

## Purpose

Repair the single global-suite failure left after r15-r3-r2-r1.  The failing
negative-path test used `config=None`, so it read the operator's real default
`.var/config/love_actions_closed_loop.ini`.  On an installed machine that file
contains the canonical factory, and the supposedly missing configuration was
not missing.

## Resolution

The test now creates an explicit empty temporary local INI and passes its path
through `config=str(local)`.  Production default discovery remains unchanged.

## Apply

The r15-r3-r2 and r15-r3-r2-r1 changes are already present in the working tree.
Do not reset them.

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r2-r2-missing-runtime-configuration-test-isolation-fix \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r2-r2-missing-runtime-configuration-test-isolation-fix \
  --commit \
  --push \
  --allow-dirty
```

## Expected result

- rules suite: green;
- global suite: the previous `test_missing_runtime_configuration...` failure is
  removed;
- configured runtime discovery still works in production;
- no runtime or backend behavior changes.
