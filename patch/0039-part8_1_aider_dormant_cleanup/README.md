# 0039 — Part 8.1 Aider Dormant Cleanup

This patch puts Aider/API work in dormant mode and adds a local cleanup tool.

## Apply

```bash
python apply_patch_queue.py --patch 0039-part8_1_aider_dormant_cleanup --dry-run
python apply_patch_queue.py --patch 0039-part8_1_aider_dormant_cleanup --commit --push
```

## After applying

Run the cleanup tool to remove generated Aider artifacts:

```bash
python tools/local_ai_dormant_cleanup.py --root . --apply --update-gitignore
git add -A
git commit -m "apply aider dormant cleanup"
git push
```

## Scope

- Add cleanup tool.
- Document Aider as dormant.
- Preserve patch queue as the active development path.
- No Scheduler, EventBus, GitHub, OpenVINO, or external API change.
