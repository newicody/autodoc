# 0275-r6-github_research_kanban_operator_model

Documentation-only phase locking the human-facing GitHub research Kanban model.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0275-r6-github_research_kanban_operator_model \
  --dry-run \
  --allow-dirty
```

Then commit only after the dry-run is green.

## Scope

- seven new documentation/rule files;
- no runtime modification;
- no non-stdlib dependency;
- no Scheduler modification;
- no GitHub mutation;
- no OpenRC service.
