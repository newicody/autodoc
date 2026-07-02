# 0015 — Phase 6.17 SourceCandidate Projection Handoff Dry-Run

This patch adds a local handoff dry-run bundle built from projection artifacts.

The bundle contains:

```text
handoff_manifest.json
projection_preview.json
projection_gate_report.json
```

## Apply

```bash
python apply_patch_queue.py --patch 0015-phase6_17_source_candidate_projection_handoff_dry_run --dry-run
python apply_patch_queue.py --patch 0015-phase6_17_source_candidate_projection_handoff_dry_run --commit --push
```

## Scope

- Add pure local handoff dry-run module.
- Add local manifest / preview / gate report bundle.
- Add tests, rules, docs and DOT.

## Out of scope

- No external API.
- No network.
- No project tracker mutation.
- No Qdrant.
- No LLM/OpenVINO.
- No Scheduler change.
- No new CLI.
