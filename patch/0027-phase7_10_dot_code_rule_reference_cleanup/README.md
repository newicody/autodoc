# 0027 — Phase 7.10 DOT code_rule Reference Cleanup

This patch adds a controlled cleanup tool for architecture DOT graphs.

It removes lines mentioning:

```text
code_rule
code-rule
code rule
```

from `.dot` files under `doc/docs/architecture`.

## Apply patch

```bash
python apply_patch_queue.py --patch 0027-phase7_10_dot_code_rule_reference_cleanup --dry-run
python apply_patch_queue.py --patch 0027-phase7_10_dot_code_rule_reference_cleanup --commit --push
```

## Then run the DOT cleanup

```bash
python tools/dot_remove_code_rule_references.py   --root .   --apply   --check   --report-file doc/maintenance/dot_code_rule_cleanup_report.json
```

## Validate after cleanup

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_dot_remove_code_rule_references.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Commit cleanup result

```bash
git add -A
git commit -m phase7-10-dot-code-rule-reference-cleanup-apply
git push
```

## Scope

- Add DOT cleanup tool.
- Remove code_rule/code-rule/code rule references from DOT graphs after command.
- Do not touch SVG files.
- Do not touch Scheduler/runtime paths.
