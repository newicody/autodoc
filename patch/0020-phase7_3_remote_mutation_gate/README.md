# 0020 — Phase 7.3 Remote Mutation Gate

This patch adds a local remote mutation gate for future adapter apply paths.

The gate is closed by default and requires explicit policy enablement, operator
confirmation and a repository allowlist.

## Apply

```bash
python apply_patch_queue.py --patch 0020-phase7_3_remote_mutation_gate --dry-run
python apply_patch_queue.py --patch 0020-phase7_3_remote_mutation_gate --commit --push
```

## Scope

- Add local remote mutation gate module.
- Add closed-by-default policy.
- Add repository allowlist and operator confirmation checks.
- Add tests, rules, docs and DOT.

## Out of scope

- No GitHub API calls.
- No network.
- No token handling.
- No remote mutation.
- No adapter apply.
- No Scheduler change.
