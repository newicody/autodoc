# 0016 — Phase 6.18 SourceCandidate Phase 6 Closure Audit

This patch adds the final local closure audit before Part 7.

It reads a handoff dry-run bundle and writes a local closure audit JSON artifact.

## Apply

```bash
python apply_patch_queue.py --patch 0016-phase6_18_source_candidate_phase6_closure_audit --dry-run
python apply_patch_queue.py --patch 0016-phase6_18_source_candidate_phase6_closure_audit --commit --push
```

## Scope

- Add pure local closure audit module.
- Validate handoff manifest, projection preview and gate report.
- Add stable JSON audit output.
- Add tests, rules, docs and DOT.

## Out of scope

- No external API.
- No network.
- No project tracker mutation.
- No Qdrant.
- No LLM/OpenVINO.
- No Scheduler change.
- No new CLI.
