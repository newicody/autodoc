# 0026 — Phase 7.9 Read-Only External Probe

This patch adds a fake-only read-only external probe boundary.

It builds a probe request from the operator external review report and runs a
fake adapter that never contacts an external service.

## Apply

```bash
python apply_patch_queue.py --patch 0026-phase7_9_read_only_external_probe --dry-run
python apply_patch_queue.py --patch 0026-phase7_9_read_only_external_probe --commit --push
```

## Scope

- Add read-only external probe request/result models.
- Add fake read-only probe adapter.
- Build probe requests from operator external review reports.
- Use post-migration doc layout paths.
- Add tests, rules, docs and DOT.

## Out of scope

- No real external adapter.
- No external API calls.
- No network.
- No token handling.
- No remote mutation.
- No Scheduler change.
