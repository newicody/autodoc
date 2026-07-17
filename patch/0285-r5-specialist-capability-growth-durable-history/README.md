# 0285-r5-specialist-capability-growth-durable-history

## Objective

Add the append-only durable-history boundary identified by phase 0285-r1, using the
r2 proposal, r3 revision lineage and r4 operator decision without selecting a runtime
revision or adding another orchestrator.

## Dependencies

The checkout must already contain:

- `0285-r2-specialist-capability-growth-proposal-contract`;
- `0285-r3-portable-specialist-revision-lineage-contract`;
- `0285-r4-specialist-capability-growth-operator-gate`;
- the 0284 portable specialist descriptor contract;
- the cumulative Projects installation guide at version 0284-r9.

## Boundaries

This patch is addition-only. SQL is the authoritative destination by contract, but the
included deterministic adapter is test-only and reports `durable=false`. It performs
no SQL write, Qdrant projection, EventBus publication, Scheduler selection or dispatch,
laboratory execution, GitHub mutation or ProjectV2 update.

## Validation performed

- new r5 context and rules tests: 18 passed;
- cumulative r2+r3+r4+r5 targeted tests: 70 passed;
- compileall: passed;
- git diff --check: passed;
- git apply --check and reapplication on an isolated compatible base: passed.

## Projects installation guide

`templates/github/projects-repository/INSTALLATION.md` was reviewed. It remains at
version 0284-r9 and is not modified because r5 changes no workflow, form, ProjectV2
field, variable, secret or deployment procedure.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0285-r5-specialist-capability-growth-durable-history \
  --commit \
  --push \
  --allow-dirty
```

Patch SHA-256: `fb00955608125144798e5e6c36bb4e4caddba906f834129beb2e119b6aa92c12`
