# 0059 — Part 12.1 Baby Fork Smoke Project Context Flow

This patch moves the minimal real baby-fork smoke project ahead of generalized Qdrant vector-space work.

## Apply

```bash
python apply_patch_queue.py --patch 0059-part12_1_baby_fork_smoke_project_context_flow --dry-run
python apply_patch_queue.py --patch 0059-part12_1_baby_fork_smoke_project_context_flow --commit --push
```

## Scope

- Add one TaskContext.
- Add one stdlib RetrievalWorker stand-in.
- Add MVTC producing exactly two variants.
- Add ContextGate applying one patch.
- Feed Cell Lens from this real flow, not the synthetic generator.
- Verify retrieval replaces calculation for this single domain before generalizing.

## Out of scope

- No Qdrant dependency.
- No seven-vector-space implementation.
- No model dependency.
- No live system adapter.
- No command gateway implementation.
