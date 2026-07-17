# 0287-r7-r8-r5 — context revision task-impact policy

Apply after `0287-r7-r8-r4-hybrid-retrieval-sql-rehydration`.

This patch adds versioned task/revision bindings, semantic change sets,
reference-level impact assessments and effect-free Scheduler decision proposals.
It does not execute Scheduler work or modify EventBus, ControlProxy, SQL, Qdrant,
OpenVINO, GitHub or the Projects deployment bundle.

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r8-r5-context-revision-task-impact-policy \
  --dry-run \
  --allow-dirty
```
