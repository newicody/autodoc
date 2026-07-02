# 0022 — Phase 7.5 GitHub Export Bundle

This patch adds a local GitHub export bundle for operator inspection.

The bundle contains:

```text
manifest.json
external_projection_contract.json
github_projection_payload.json
remote_mutation_gate.json
github_adapter_dry_run.json
```

## Apply

```bash
python apply_patch_queue.py --patch 0022-phase7_5_github_export_bundle --dry-run
python apply_patch_queue.py --patch 0022-phase7_5_github_export_bundle --commit --push
```

## Scope

- Add local GitHub export bundle module.
- Copy contract and GitHub payload artifacts.
- Write remote mutation gate result.
- Write fake adapter dry-run result.
- Add tests, rules, docs and DOT.

## Out of scope

- No real GitHub adapter.
- No GitHub API calls.
- No network.
- No token handling.
- No remote mutation.
- No Scheduler change.
