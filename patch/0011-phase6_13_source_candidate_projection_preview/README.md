# 0011 — Phase 6.13 SourceCandidate Projection Preview

This patch adds a local projection preview generated from the SourceCandidate operator report.

It prepares a future external project surface without contacting or mutating any external service.

## Apply

```bash
python apply_patch_queue.py --patch 0011-phase6_13_source_candidate_projection_preview --dry-run
python apply_patch_queue.py --patch 0011-phase6_13_source_candidate_projection_preview --commit --push
```

## Scope

- Add pure projection preview module.
- Add atomic local JSON writer.
- Add tests and rules.
- Add docs and DOT.

## Out of scope

- No external API.
- No network.
- No project tracker mutation.
- No Qdrant.
- No LLM/OpenVINO.
- No Scheduler change.
