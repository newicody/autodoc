# Changelog — Part 8.0 Roadmap B Aider Orchestrator

## Added

- `tools/roadmap_b_aider_orchestrator.py`
  - Selects Roadmap B steps.
  - Builds Aider prompts.
  - Asks Aider to create patch bundles.
  - Inspects generated patch diffs.
  - Applies patches with `apply_patch_queue.py`.
  - Runs tests after each step.
  - Requests operator approval for sensitive changes.

- `doc/maintenance/ROADMAP_B_LOCK.md`
  - Locks Roadmap B as the current development direction.

- `doc/maintenance/ROADMAP_B_AIDER_ORCHESTRATOR.md`
  - Documents usage and validation gates.

- Tests for tools and rules.

## Not added

- No Scheduler integration.
- No external service adapter.
- No remote mutation.
- No DOT.
- No SVG.
