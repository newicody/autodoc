# 0010 — Phase 6.12 SourceCandidate Operator CLI Help Gate

This patch adds a small regression gate for the unified SourceCandidate operator CLI introduced in Phase 6.11.

It is intentionally additive and does not change the Scheduler, stores, external integrations, Qdrant, LLM, or OpenVINO paths.

## Apply

```bash
python apply_patch_queue.py --patch 0010-phase6_12_source_candidate_operator_cli_help_gate --dry-run
python apply_patch_queue.py --patch 0010-phase6_12_source_candidate_operator_cli_help_gate --commit --push
```

## Gate

```bash
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src pytest -q tests/context/test_source_candidate_operator_cli_help.py
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```
