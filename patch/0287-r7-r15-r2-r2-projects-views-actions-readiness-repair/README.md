# 0287-r7-r15-r2-r2 — Projects views and Actions readiness repair

## Purpose

Repair the copied `newicody/projects` installation boundary before live r15
execution. The patch adds an exact read-only audit for ProjectV2 views/fields
and GitHub Actions readiness, and fixes the cumulative installation guide so it
uses the real reconciliation digest.

A view is no longer considered compliant solely because its name exists.
Layout, filter, visible fields, board column and vertical grouping are compared
against the declared configuration.

## Base

Apply after:

```text
0287-r7-r15-r2-r1-automatic-projectv2-runtime-resolution
```

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r2-projects-views-actions-readiness-repair \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r2-projects-views-actions-readiness-repair \
  --commit \
  --push \
  --allow-dirty
```

## Synchronize the Projects bundle

After applying the patch in `autodoc`, copy/update the cumulative bundle into
`/home/eric/projet/git/projects` using the repository's existing installation
procedure, then commit and push the Projects repository changes.

## Exact read-only diagnostic

From the installed `newicody/projects` checkout:

```bash
python scripts/check_projects_bundle_readiness.py \
  --config projectv2_views.json \
  --workflow .github/workflows/autodoc-controlled-research.yml \
  --repository newicody/projects \
  --format json | \
tee /tmp/projects-bundle-readiness.json
```

Useful summary:

```bash
jq '{
  projectv2_exact,
  authoritative_ready,
  copilot_ready,
  full_ready,
  workflow: {
    manual_dispatch_only: .workflow_readiness.workflow.manual_dispatch_only,
    blocked_actions: .workflow_readiness.blocked_actions,
    actions_policy: .workflow_readiness.actions_policy,
    copilot: .workflow_readiness.copilot
  },
  issues,
  warnings
}' /tmp/projects-bundle-readiness.json
```

The command performs no mutation. It returns success when the authoritative
request/artifact path is ready. `copilot_ready=false` remains visible but does
not fail that path when Copilot is intentionally disabled.

## Reconciliation digest

The installation guide now records the required sequence:

```text
preview
→ extract .plan_digest
→ require a non-empty digest
→ execute with the same digest
```

Do not pass `<PLAN_DIGEST>` or an empty string literally.

## Expected validation

```bash
python -m compileall -q \
  templates/github/projects-repository/scripts \
  tests/tools/test_projects_bundle_readiness_0287_r7_r15_r2_r2.py \
  tests/rules/test_projects_bundle_readiness_0287_r7_r15_r2_r2_rule.py

PYTHONPATH=templates/github/projects-repository/scripts:. \
python -m pytest -q \
  tests/tools/test_projects_bundle_readiness_0287_r7_r15_r2_r2.py \
  tests/rules/test_projects_bundle_readiness_0287_r7_r15_r2_r2_rule.py

python -m pytest -q tests/rules
python -m pytest -q
```

## Suggested commit subject

```text
repair Projects views and Actions readiness diagnostics
```

## Next patch

`0287-r7-r15-r3-r1-installed-runtime-factory-composition` binds the existing
Scheduler, SQL authority, OpenVINO/E5-384 and Qdrant ports into the canonical
installed runtime factory required by the live preview.
