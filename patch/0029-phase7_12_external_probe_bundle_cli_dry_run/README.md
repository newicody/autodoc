# 0029 — Phase 7.12 External Probe Bundle CLI Dry-Run

This patch adds a CLI for the local external probe bundle.

The CLI is dry-run by default. It writes the local bundle only when `--apply`
is passed.

## Apply

```bash
python apply_patch_queue.py --patch 0029-phase7_12_external_probe_bundle_cli_dry_run --dry-run
python apply_patch_queue.py --patch 0029-phase7_12_external_probe_bundle_cli_dry_run --commit --push
```

## Scope

- Add external probe bundle CLI.
- Keep dry-run as the default mode.
- Support JSON and text output.
- Add tests, rules and documentation.

## Out of scope

- No external service calls.
- No network.
- No remote mutation.
- No Scheduler change.
- No SVG regeneration policy change yet.
