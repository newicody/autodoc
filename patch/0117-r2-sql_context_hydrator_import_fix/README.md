# 0117-r2 — SQLContextHydrator import fix

This corrective patch fixes the 0117 import style so the repository rule `stdlib_first_no_unapproved_external_imports` does not detect `src` as an external import root.

It changes `src.context...` imports to internal `context...` imports in the new hydrator module and its runtime test.

Use this patch after a failed 0117 apply where `git apply` already modified the working tree and rule tests failed.

## Apply

```bash
python apply_patch_queue.py --patch 0117-r2-sql_context_hydrator_import_fix --dry-run --allow-dirty
python apply_patch_queue.py --patch 0117-r2-sql_context_hydrator_import_fix --commit --push --allow-dirty
```

## Validate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_sql_context_hydrator.py
PYTHONPATH=src:. pytest -q tests/rules/test_sql_context_hydrator_0117_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
