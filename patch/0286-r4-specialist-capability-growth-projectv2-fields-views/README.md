# 0286-r4 — Specialist capability-growth ProjectV2 fields/views

This unit extends the versioned `newicody/projects` bundle with the nine
specialist capability-growth review fields and the table view
`Révisions spécialistes`.

## Boundaries

- GitHub Projects remains a non-authoritative review/workflow surface.
- SQL remains the durable authority.
- The existing Scheduler remains the only orchestration authority.
- Qdrant remains projection/recall only.
- No workflow, permission, secret, variable, backend, Scheduler, registry,
  EventBus or laboratory runtime is added.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0286-r4-specialist-capability-growth-projectv2-fields-views \
  --dry-run \
  --allow-dirty
```

Then, after a green dry-run:

```bash
python apply_patch_queue.py \
  --patch 0286-r4-specialist-capability-growth-projectv2-fields-views \
  --commit \
  --push \
  --allow-dirty
```

## Targeted verification

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_specialist_capability_growth_projectv2_fields_views_0286.py \
  tests/rules/test_specialist_capability_growth_projectv2_fields_views_0286_rule.py
```

The patch expects the 0286-r3 request-form unit and its audit-progression rule
fix to be present.
