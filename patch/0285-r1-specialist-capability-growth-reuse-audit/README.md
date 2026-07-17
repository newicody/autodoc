# 0285-r1 — specialist capability growth reuse audit

## Prerequisite

Apply this patch after:

- `0284-r9-specialists-laboratories-live-path-evidence`;
- `0284-r9-r2-specialists-laboratories-documentation-compatibility-markers`.

The patch adds new files only. It does not modify runtime code, the Scheduler,
laboratory providers, SQL/Qdrant/OpenVINO adapters, GitHub workflows, or
`templates/github/projects-repository/INSTALLATION.md`.

## Purpose

Audit the current reusable architecture and lock the controlled 0285 sequence:

`proposal → evidence → operator decision → immutable revision → durable history → approved Scheduler selection → passive observation → closed-loop smoke`

The audit is source-only and recommends
`0285-r2-specialist-capability-growth-proposal-contract` as the next patch.

## Apply

From the repository root, after extracting this archive:

```bash
python apply_patch_queue.py \
  --patch 0285-r1-specialist-capability-growth-reuse-audit \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0285-r1-specialist-capability-growth-reuse-audit \
  --commit \
  --push \
  --allow-dirty
```

## Focused validation

```bash
PYTHONPATH=src python -m pytest -q \
  tests/context/test_specialist_capability_growth_reuse_audit_0285.py \
  tests/rules/test_specialist_capability_growth_reuse_audit_0285_rule.py

python tools/run_specialist_capability_growth_reuse_audit_0285.py \
  --root . \
  --format summary
```
