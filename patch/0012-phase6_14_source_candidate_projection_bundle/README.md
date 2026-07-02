# 0012 — Phase 6.14 SourceCandidate Projection Bundle

This patch adds a local projection bundle built from an operator report file.

It builds on Phase 6.13 projection preview and writes:

```text
manifest.json
projection_preview.json
```

## Apply

```bash
python apply_patch_queue.py --patch 0012-phase6_14_source_candidate_projection_bundle --dry-run
python apply_patch_queue.py --patch 0012-phase6_14_source_candidate_projection_bundle --commit --push
```

## Scope

- Add pure local projection bundle module.
- Add atomic manifest/preview output.
- Add tests and rules.
- Add docs and DOT.

## Out of scope

- No external API.
- No network.
- No project tracker mutation.
- No Qdrant.
- No LLM/OpenVINO.
- No Scheduler change.
