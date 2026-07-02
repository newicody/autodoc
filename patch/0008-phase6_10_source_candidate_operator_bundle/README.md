# 0008 — Phase 6.10 SourceCandidate Operator Bundle

This patch adds a local bundle writer for SourceCandidate operator reports.

## Scope

- Build a local bundle directory from the existing operator report path.
- Write `manifest.json` plus JSON/text report artifacts.
- Keep the feature local-only and deterministic.
- Add tests, rule tests, architecture DOT, changelog, release README, and test report.

## Non-scope

- No external API.
- No project tracker integration.
- No vector database.
- No model inference.
- No Scheduler modification.

## Apply

```bash
python apply_patch_queue.py --patch 0008-phase6_10_source_candidate_operator_bundle --dry-run
python apply_patch_queue.py --patch 0008-phase6_10_source_candidate_operator_bundle --commit --push
```

## Manual gate

```bash
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src pytest -q tests/context/test_source_candidate_operator_bundle.py
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```
