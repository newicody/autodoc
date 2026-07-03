# 0058-r2 — Part 11.2 Runtime Token Zone Context Qdrant Plan

This patch replaces the previous 0058 architecture plan with the corrected version.

## Apply

```bash
python apply_patch_queue.py --patch 0058-r2-part11_2_runtime_token_zone_context_qdrant_plan --dry-run
python apply_patch_queue.py --patch 0058-r2-part11_2_runtime_token_zone_context_qdrant_plan --commit --push
```

## Scope

- Update the global architecture plan.
- Reframe MVTC as context variation/testing, not only risk.
- Place Qdrant as vector projection memory with core/work/lab instances.
- Place language models as workers/experts.
- Correct the event rule to no event-to-action shortcut.
- Add the baby fork example and R2 roadmap.

## Out of scope

- No runtime implementation.
- No Qdrant dependency.
- No model dependency.
- No Scheduler change.
- No EventBus change.
