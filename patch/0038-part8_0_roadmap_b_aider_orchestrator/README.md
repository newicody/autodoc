# 0038 — Part 8.0 Roadmap B Aider Orchestrator

This patch adds a Python orchestrator for Roadmap B using Aider as the patch-bundle author.

## Apply

```bash
python apply_patch_queue.py --patch 0038-part8_0_roadmap_b_aider_orchestrator --dry-run
python apply_patch_queue.py --patch 0038-part8_0_roadmap_b_aider_orchestrator --commit --push
```

## Scope

- Lock Roadmap B in documentation.
- Add Python orchestrator.
- Use Aider to create patch bundles.
- Apply generated bundles through apply_patch_queue.py.
- Run tests after each step.
- Require operator validation for rules, dependencies, Scheduler/runtime paths and large retroactive changes.

## Out of scope

- No Scheduler integration.
- No real external integration.
- No remote mutation.
- No DOT.
- No SVG.
