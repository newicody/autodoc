# 0034 — Phase 7.17 External Probe Local Audit Trail

This patch adds a local JSONL audit trail for external probe operator summaries.

## Apply

```bash
python apply_patch_queue.py --patch 0034-phase7_17_external_probe_local_audit_trail --dry-run
python apply_patch_queue.py --patch 0034-phase7_17_external_probe_local_audit_trail --commit --push
```

## Scope

- Add local audit trail module.
- Add CLI for recording operator summaries.
- Append JSONL audit events.
- Write compact audit reports.
- Add tests, rules and documentation.

## Out of scope

- No external calls.
- No network.
- No remote mutation.
- No Scheduler change.
- No DOT.
- No SVG.
