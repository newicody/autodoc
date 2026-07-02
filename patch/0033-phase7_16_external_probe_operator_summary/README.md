# 0033 — Phase 7.16 External Probe Operator Summary

This patch adds a local operator summary for external probe artifact indexes.

## Apply

```bash
python apply_patch_queue.py --patch 0033-phase7_16_external_probe_operator_summary --dry-run
python apply_patch_queue.py --patch 0033-phase7_16_external_probe_operator_summary --commit --push
```

## Scope

- Add local external probe operator summary module.
- Add CLI for summary generation.
- Group indexed bundles into ready/check/blocked.
- Add tests, rules and documentation.

## Out of scope

- No external calls.
- No network.
- No remote mutation.
- No Scheduler change.
- No DOT.
- No SVG.
