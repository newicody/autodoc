# 0028 — Phase 7.11 External Probe Bundle

This patch adds a local bundle for read-only external probe artifacts.

The bundle contains:

```text
manifest.json
operator_external_review_report.json
read_only_external_probe_request.json
read_only_external_probe_result.json
```

## Apply

```bash
python apply_patch_queue.py --patch 0028-phase7_11_external_probe_bundle --dry-run
python apply_patch_queue.py --patch 0028-phase7_11_external_probe_bundle --commit --push
```

## Scope

- Add local external probe bundle model.
- Copy local read-only probe artifacts into one deterministic directory.
- Write a manifest.
- Preserve read-only and external-call flags.
- Add tests, rules, docs and DOT.

## Out of scope

- No real external adapter.
- No external API calls.
- No network.
- No remote mutation.
- No Scheduler change.
- No code_rule references in DOT diagrams.
