# 0013 — Phase 6.15 SourceCandidate Projection Gate

This patch adds a local validation gate for projection bundles.

It validates bundle manifest and preview consistency before any future external handoff.

## Apply

```bash
python apply_patch_queue.py --patch 0013-phase6_15_source_candidate_projection_gate --dry-run
python apply_patch_queue.py --patch 0013-phase6_15_source_candidate_projection_gate --commit --push
```

## Scope

- Add pure local projection gate module.
- Validate manifest/preview schemas and item counts.
- Add optional audit-present requirement.
- Add tests, rules, docs and DOT.

## Out of scope

- No external API.
- No network.
- No project tracker mutation.
- No Qdrant.
- No LLM/OpenVINO.
- No Scheduler change.
