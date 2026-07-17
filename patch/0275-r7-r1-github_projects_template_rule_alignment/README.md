# 0275-r7-r1-github_projects_template_rule_alignment

Microfix for the two textual rule failures reported after 0275-r7.

## Apply on the current dirty working tree

```bash
python apply_patch_queue.py \
  --patch 0275-r7-r1-github_projects_template_rule_alignment \
  --dry-run \
  --allow-dirty
```

Then commit only after all tests are green.
