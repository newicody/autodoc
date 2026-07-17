# 0287-r7-r15-r2-r2-r2 — Projects installation remaining compatibility markers fix

## Purpose

This corrective patch is applied after both:

- `0287-r7-r15-r2-r2-projects-views-actions-readiness-repair`;
- `0287-r7-r15-r2-r2-r1-projects-installation-budget-compatibility-fix`.

Those units are already present in the working tree but the patch queue stopped
before commit because six historical markers were still missing from the
compressed cumulative guide.

This patch restores only those markers:

- `## Compatibilité cumulative 0287-r5-r2-r2`;
- `publish_github_advisory_issue_comment_0281.py`;
- the exact `| `0284-r9` |` historical row;
- `verify_specialists_laboratories_live_path_evidence_0284.py`.

`INSTALLATION.md` remains at 379 lines, below the locked 380-line budget. The
preview-derived `$PLAN_DIGEST` command and Copilot-safe ordering remain intact.

## Apply on the current dirty tree

Do not reset the already-applied r15-r2-r2 and r15-r2-r2-r1 changes.

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r2-r2-projects-installation-remaining-compatibility-markers-fix \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r2-r2-projects-installation-remaining-compatibility-markers-fix \
  --commit \
  --push \
  --allow-dirty
```

The resulting commit is expected to include the readiness patch and its two
successive documentation compatibility fixes together.

Suggested commit message:

```text
restore remaining Projects installation compatibility markers
```

## Validation performed

```text
git diff --check                          OK
git apply --check on current r1 tree      OK
compileall targeted                        OK
available tests/rules                      49 passed
six reported marker assertions             OK
INSTALLATION.md line count                 379
Copilot false-before-true ordering          OK
real digest command preserved               OK
Graphviz source only                        OK
no generated SVG or binary patch            OK
```
