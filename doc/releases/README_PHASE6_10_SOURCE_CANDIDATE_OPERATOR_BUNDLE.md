# Phase 6.10 — SourceCandidate Operator Bundle

Phase 6.10 adds a local bundle directory for SourceCandidate operator reports.

The operator can now generate a stable local bundle containing:

```text
manifest.json
operator_report.json
operator_report.txt
```

Example:

```bash
PYTHONPATH=src python -m context.source_candidate_operator_bundle_cli \
  --store-file /tmp/source_candidates.json \
  --audit-dir /tmp/source_candidate_audits \
  --bundle-dir /tmp/source_candidate_operator_bundle \
  --format json
```

The feature is local-only and does not contact external systems.
