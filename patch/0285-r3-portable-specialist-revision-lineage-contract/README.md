# 0285-r3-portable-specialist-revision-lineage-contract

## Objective

Add the immutable portable-specialist revision and lineage contracts identified by
phase 0285-r1, directly after the r2 evidence-backed proposal contract.

## Dependencies

The checkout must already contain:

- `0285-r2-specialist-capability-growth-proposal-contract`;
- the 0284 portable specialist descriptor contract;
- the cumulative Projects installation guide at version 0284-r9.

## Boundaries

This patch is addition-only. It does not modify Scheduler, SQL, Qdrant, OpenVINO,
EventBus, laboratory runtimes, GitHub workflows or ProjectV2 configuration.

## Validation performed

- targeted context and rules tests: 19 passed;
- compileall: passed;
- git diff --check: passed;
- git apply --check on an isolated compatible base: passed.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0285-r3-portable-specialist-revision-lineage-contract \
  --commit \
  --push \
  --allow-dirty
```

Patch SHA-256: `cfd1739f565895c1285465daf0bdde14d97963a481d80be21eeceab7a03598e7`
