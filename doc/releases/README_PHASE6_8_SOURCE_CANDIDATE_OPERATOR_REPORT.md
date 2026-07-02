# Phase 6.8 — SourceCandidate Operator Report CLI

Phase 6.8 adds a local operator report projection.

It combines review and audit information into a compact report suitable for an operator handoff:

```bash
PYTHONPATH=src python -m context.source_candidate_operator_report_cli \
  --store-file /tmp/source_candidates.json \
  --include-terminal \
  --audit-dir /tmp/source_candidate_audits \
  --format text
```

JSON output is also available:

```bash
PYTHONPATH=src python -m context.source_candidate_operator_report_cli \
  --store-file /tmp/source_candidates.json \
  --include-terminal \
  --audit-dir /tmp/source_candidate_audits \
  --format json
```

The phase remains local-only and does not add any external backend.
