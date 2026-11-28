# Phase 6.7 — SourceCandidate Review Audit Summary

Phase 6.7 adds an operator projection that combines:

- the local SourceCandidate review queue;
- the decision stored on each candidate;
- optional local decision audit JSON files.

The feature is intentionally local-only. It does not contact a remote service and does not change the Scheduler.

Example:

```bash
PYTHONPATH=src python -m context.source_candidate_review_audit_cli \
  --store-file /tmp/source_candidates.json \
  --include-terminal \
  --audit-dir /tmp/source_candidate_audits \
  --format json
```
