# 0004 — Phase 6.6 SourceCandidate Decision Audit / Report

This patch extends the local SourceCandidate decision live path with an optional audit report artifact.

## Scope

- Add a stable local JSON audit report for explicit operator decisions.
- Keep the existing Scheduler-first decision path unchanged.
- Add CLI flags for audit generation.
- Add tests and rule checks.
- Add release documentation and architecture DOT source.

## Non-goals

- No external API call.
- No project board mutation.
- No vector database.
- No LLM or model runtime.
- No Scheduler modification.
- No generated SVG versioning.

## Apply

```bash
python apply_patch_queue.py --patch 0004-phase6_6_source_candidate_decision_audit --dry-run
python apply_patch_queue.py --patch 0004-phase6_6_source_candidate_decision_audit
```

## Verify

```bash
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src pytest -q tests/context/test_source_candidate_decision_audit.py
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Commit

```bash
git commit -m "phase6.6 add source candidate decision audit report"
```
