# 0275-r8-project_status_en_cours_dispatch_copilot_groups

Reuse the 0272 ProjectV2 snapshot/diff path to dispatch the controlled
`newicody/projects` workflow once when a card enters `En cours`. Activate
Copilot with the ephemeral Actions token and document theme hierarchy boxes.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0275-r8-project_status_en_cours_dispatch_copilot_groups \
  --dry-run \
  --allow-dirty
```

Stop at the first failing gate.
