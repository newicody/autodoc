# 0035 — Phase 7.18 External Probe Local Replay

This patch adds local replay for the external probe audit trail.

## Apply

```bash
python apply_patch_queue.py --patch 0035-phase7_18_external_probe_local_replay --dry-run
python apply_patch_queue.py --patch 0035-phase7_18_external_probe_local_replay --commit --push
```

## Scope

- Add local replay module.
- Add CLI for replay reports.
- Replay JSONL audit events.
- Add tests, rules and documentation.

## Out of scope

- No external calls.
- No network.
- No remote mutation.
- No Scheduler change.
- No DOT.
- No SVG.
