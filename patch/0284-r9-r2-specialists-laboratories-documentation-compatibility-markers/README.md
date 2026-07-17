# 0284-r9-r2 — documentation compatibility markers

Apply this replacement after the failed queue attempt for
`0284-r9-r1-specialists-laboratories-rule-compatibility-fix`.

The r1 patch failed during `git apply --check`, so none of its files were
applied. The original `0284-r9` files remain present in the dirty working tree.

This patch deliberately does not modify
`tests/rules/test_projects_installation_copilot_safe_default_0284_rule.py`.
Instead it:

- restores the 0281/0282 markers required by the two roadmap rules;
- keeps `INSTALLATION.md` at current version `0284-r9`;
- records the exact `0284-r1-r5` declaration as a historical compatibility
  sentence after the r9 history row;
- adds a non-brittle rule that distinguishes current and historical versions.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0284-r9-r2-specialists-laboratories-documentation-compatibility-markers \
  --commit \
  --push \
  --allow-dirty
```

Do not reapply `0284-r9`, and do not apply the failed r1 patch first.
