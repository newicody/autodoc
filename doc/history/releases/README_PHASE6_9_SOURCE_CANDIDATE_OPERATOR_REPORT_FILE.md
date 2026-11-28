# Phase 6.9 — SourceCandidate Operator Report File Artifact

Phase 6.9 adds a local artifact writer for the SourceCandidate operator report.

The operator can now generate a stable JSON or text file from the existing review/audit/report path:

```bash
PYTHONPATH=src python -m context.source_candidate_operator_report_file_cli \
  --store-file /tmp/source_candidates.json \
  --audit-dir /tmp/source_candidate_audits \
  --output-file /tmp/operator_report.json \
  --format json
```

The feature is local-only and does not contact external systems.
