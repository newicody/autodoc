# 0281-r6-controlled-advisory-issue-publication

## Repository impact

```text
autodoc: change required
projects: no Git-tracked change required
projects_repository_change_required: false
workflow permissions remain unchanged
```

The Issue comment is published by the local Autodoc operator adapter, not by
the GitHub Actions producer.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0281-r6-controlled-advisory-issue-publication \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0281-r6-controlled-advisory-issue-publication \
  --commit \
  --push \
  --allow-dirty
```

## Focused tests

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_controlled_advisory_issue_publication_0281.py \
  tests/tools/test_publish_github_advisory_issue_comment_0281.py \
  tests/rules/test_github_controlled_advisory_issue_publication_0281_rule.py
```

## Publication model

1. produce an r5 `publication_preview` JSON;
2. run the tool without `--execute`;
3. review the rendered body and copy `plan_digest`;
4. rerun with `--execute --confirm-plan-digest <exact digest>`.

The local `gh` identity must have Issue write permission.
