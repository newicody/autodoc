# 0037 — Phase 7.20 Freeze + Handoff Contract

This patch freezes Part 7 and adds the local handoff contract for Part 8.

## Apply

```bash
python apply_patch_queue.py --patch 0037-phase7_20_freeze_handoff_contract --dry-run
python apply_patch_queue.py --patch 0037-phase7_20_freeze_handoff_contract --commit --push
```

## Scope

- Add Phase 7 handoff contract module.
- Add CLI for contract generation.
- Validate optional Phase 7 closure report.
- Freeze external and autonomous boundaries.
- Add tests, rules and documentation.

## Out of scope

- No external calls.
- No network.
- No remote mutation.
- No Scheduler change.
- No DOT.
- No SVG.
