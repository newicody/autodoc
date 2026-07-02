# 0019 — Phase 7.2 GitHub Projection Payload Dry-Run

This patch adds a local GitHub-shaped projection payload built from the
target-neutral external projection contract.

It remains dry-run only:

```text
dry_run: true
remote_mutation: false
```

## Apply

```bash
python apply_patch_queue.py --patch 0019-phase7_2_github_projection_payload_dry_run --dry-run
python apply_patch_queue.py --patch 0019-phase7_2_github_projection_payload_dry_run --commit --push
```

## Scope

- Add GitHub-shaped dry-run payload module.
- Add issue creation intents.
- Preserve safety flags as labels.
- Add tests, rules, docs and DOT.

## Out of scope

- No GitHub API calls.
- No network.
- No token handling.
- No remote mutation.
- No adapter apply.
- No Scheduler change.
