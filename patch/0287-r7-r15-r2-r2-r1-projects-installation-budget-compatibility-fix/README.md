# 0287-r7-r15-r2-r2-r1 — Projects installation budget compatibility fix

## Purpose

This corrective patch is applied **after**
`0287-r7-r15-r2-r2-projects-views-actions-readiness-repair` has already been
applied to the working tree and failed `tests/rules`.

It fixes the seven reported compatibility failures without reverting the new
ProjectV2/Actions readiness implementation:

- `INSTALLATION.md` is reduced from 492 to 375 lines;
- `AUTODOC_COPILOT_ADVISORY_ENABLED=false` again precedes the optional `true`;
- the real execution command uses `--confirm-plan-digest "$PLAN_DIGEST"`;
- historical placeholder strings are retained exactly once under a
  **ne pas exécuter** compatibility heading;
- the r15-r2-r2 rule is updated to verify placement instead of global absence.

## Apply on the current dirty tree

Do not reset the already-applied r15-r2-r2 files. From the Autodoc checkout:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r2-r1-projects-installation-budget-compatibility-fix \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r2-r1-projects-installation-budget-compatibility-fix \
  --commit \
  --push \
  --allow-dirty
```

The resulting commit is expected to include the previously applied r15-r2-r2
readiness files and this corrective unit together.

Suggested commit message:

```text
repair Projects installation compatibility budget
```

## Validation performed

```text
git apply --check                         OK
application on r15-r2-r2 tree             OK
compileall targeted                        OK
tests/rules in available mirror            46 passed
readiness tool tests                         9 passed
INSTALLATION.md line count                 375
legacy placeholder placement               OK
Copilot false-before-true ordering          OK
Graphviz source only                        OK
no generated SVG or binary patch            OK
```
