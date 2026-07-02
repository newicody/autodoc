# 0021 — Phase 7.4 GitHub Adapter Interface Fake-Only

This patch adds the GitHub adapter interface and a fake-only local implementation.

The fake adapter supports:

```text
plan
dry_run
apply
```

Apply remains a local simulation and is allowed only when the remote mutation gate passes.

## Apply

```bash
python apply_patch_queue.py --patch 0021-phase7_4_github_adapter_interface_fake_only --dry-run
python apply_patch_queue.py --patch 0021-phase7_4_github_adapter_interface_fake_only --commit --push
```

## Scope

- Add GitHub adapter protocol.
- Add fake-only local adapter.
- Route dry-run/apply through remote mutation gate.
- Add tests, rules, docs and DOT.

## Out of scope

- No real GitHub adapter.
- No GitHub API calls.
- No network.
- No token handling.
- No real remote mutation.
- No Scheduler change.
