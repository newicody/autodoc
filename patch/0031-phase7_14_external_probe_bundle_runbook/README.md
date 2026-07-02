# 0031 — Phase 7.14 External Probe Bundle Runbook

This patch adds an operator runbook for the local external probe bundle workflow.

## Apply

```bash
python apply_patch_queue.py --patch 0031-phase7_14_external_probe_bundle_runbook --dry-run
python apply_patch_queue.py --patch 0031-phase7_14_external_probe_bundle_runbook --commit --push
```

## Scope

- Add external probe bundle operator runbook.
- Document dry-run before apply.
- Document expected bundle files and safety flags.
- Reference the documentation SVG build policy.
- Add docs/rules tests.

## Out of scope

- No runtime module.
- No CLI change.
- No DOT.
- No SVG.
- No network.
- No Scheduler change.
