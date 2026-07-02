# 0014 — Phase 6.16 SourceCandidate Projection Gate Report

This patch adds a local JSON report artifact for projection gate results.

It is the first closure step before Part 7: projection readiness becomes explicit and reusable without contacting an external service.

## Apply

```bash
python apply_patch_queue.py --patch 0014-phase6_16_source_candidate_projection_gate_report --dry-run
python apply_patch_queue.py --patch 0014-phase6_16_source_candidate_projection_gate_report --commit --push
```

## Scope

- Add pure local projection gate report module.
- Add atomic JSON report writing.
- Add tests, rules, docs and DOT.

## Out of scope

- No external API.
- No network.
- No project tracker mutation.
- No Qdrant.
- No LLM/OpenVINO.
- No Scheduler change.
- No new CLI.
