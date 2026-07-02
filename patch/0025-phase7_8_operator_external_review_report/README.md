# 0025 — Phase 7.8 Operator External Review Report

This patch adds a local operator external review report built from the GitHub
export bundle.

The report reads:

```text
manifest.json
remote_mutation_gate.json
github_adapter_dry_run.json
```

and produces a compact operator-facing review state.

## Apply

```bash
python apply_patch_queue.py --patch 0025-phase7_8_operator_external_review_report --dry-run
python apply_patch_queue.py --patch 0025-phase7_8_operator_external_review_report --commit --push
```

## Scope

- Add operator external review report module.
- Summarize local GitHub export bundle status.
- Surface gate findings and adapter dry-run issues.
- Use post-migration doc layout paths.
- Add tests, rules, docs and DOT.

## Out of scope

- No real GitHub adapter.
- No GitHub API calls.
- No network.
- No token handling.
- No remote mutation.
- No Scheduler change.
