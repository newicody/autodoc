# 0005 — Phase 6.7 SourceCandidate Review Audit Summary

This patch adds a local operator projection that enriches SourceCandidate review output with stored decision summaries and optional local decision audit JSON files.

It does not modify the Scheduler, does not add network access, and does not write to the SourceCandidate store.

## Apply

```bash
python apply_patch_queue.py --patch 0005-phase6_7_source_candidate_review_audit_summary --dry-run
python apply_patch_queue.py --patch 0005-phase6_7_source_candidate_review_audit_summary
```

## Gate

```bash
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src pytest -q tests/context/test_source_candidate_review_audit.py
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```
