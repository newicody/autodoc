# 0285-r4-specialist-capability-growth-operator-gate

## Objective

Add the explicit approve/reject/defer operator boundary identified by phase 0285-r1,
using the r2 proposal and r3 revision-lineage contracts without adding persistence,
runtime selection or orchestration.

## Dependencies

The checkout must already contain:

- `0285-r2-specialist-capability-growth-proposal-contract`;
- `0285-r3-portable-specialist-revision-lineage-contract`;
- the 0284 portable specialist descriptor contract;
- the cumulative Projects installation guide at version 0284-r9.

## Boundaries

This patch is addition-only. An approved decision authorizes a revision for the future
r5 history, but performs no SQL write, Qdrant projection, EventBus publication,
Scheduler selection, laboratory execution, GitHub mutation or ProjectV2 update.

## Validation performed

- new r4 context and rules tests: 18 passed;
- cumulative r2+r3+r4 targeted tests: 52 passed;
- compileall: passed;
- git diff --check: passed;
- git apply --check on an isolated compatible base: passed.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0285-r4-specialist-capability-growth-operator-gate \
  --commit \
  --push \
  --allow-dirty
```

Patch SHA-256: `f6f386190ed87721bc28a05b962b85d7b8087412598dcaf9f0447e3abd6ce7bb`
