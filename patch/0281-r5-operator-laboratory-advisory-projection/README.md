# 0281-r5-operator-laboratory-advisory-projection

## Repository impact

```text
autodoc: change required
projects: no change required
projects_repository_change_required: false
```

## Apply

```bash
python apply_patch_queue.py \
  --patch 0281-r5-operator-laboratory-advisory-projection \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0281-r5-operator-laboratory-advisory-projection \
  --commit \
  --push \
  --allow-dirty
```

## Focused tests

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_operator_laboratory_advisory_projection_0281.py \
  tests/rules/test_github_operator_laboratory_advisory_projection_0281_rule.py
```

## Next phase

`0281-r6-controlled-advisory-issue-publication`.

The publication contract remains mutation-closed by default. Deployment to
`newicody/projects` will be explicitly identified in r6 if `issues: write` is
opened.
