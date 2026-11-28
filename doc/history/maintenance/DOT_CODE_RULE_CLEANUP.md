# DOT code_rule cleanup

The architecture DOT files should describe the runtime/control architecture,
not the documentation-rule audit path. References to `code_rule`, `code-rule`
or `code rule` overload the diagrams and should be removed from DOT graphs.

## Dry-run

```bash
python tools/dot_remove_code_rule_references.py \
  --root . \
  --report-file doc/maintenance/dot_code_rule_cleanup_report.json
```

## Apply

```bash
python tools/dot_remove_code_rule_references.py \
  --root . \
  --apply \
  --check \
  --report-file doc/maintenance/dot_code_rule_cleanup_report.json
```

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_dot_remove_code_rule_references.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

The cleanup must be committed with `git add -A` so DOT modifications and the
cleanup report are recorded together.
