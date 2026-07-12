# Phase 0275-r7-r2 test report — template/rule alignment

## Reported states

```text
0275-r7 rules: 2 failed, 1094 passed
0275-r7-r1 dry-run: patch did not apply
```

## Root cause of r1

The repair diff was constructed from fragments rather than the full tracked
files. Its hunk positions therefore incorrectly started at line 1.

## r2 correction

The diff is generated from the complete current versions of both modified
files and is validated with `git apply --check` in a synthetic repository
containing the exact expected 0275-r7 working-tree state.

## Validation on the real repository

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. python -m pytest -q \
  tests/rules/test_github_research_kanban_operator_model_0275_r6_rule.py \
  tests/rules/test_github_projects_research_theme_event_templates_0275_r7_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```
