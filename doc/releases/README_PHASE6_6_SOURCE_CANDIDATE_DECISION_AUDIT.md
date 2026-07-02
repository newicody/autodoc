# Phase 6.6 — SourceCandidate Decision Audit / Report

Phase 6.6 adds a local audit report after an operator decision.

Example:

```bash
PYTHONPATH=src python -m context.source_candidate_decision_cli \
  --store-file /tmp/source_candidates.json \
  --candidate-id sc-example \
  --action archive \
  --reason "handled" \
  --audit-file /tmp/source_candidate_decision_audit.json \
  --format json
```

The audit report is a deterministic JSON artifact with:

```text
schema
operation
store_path
candidate_id
action
before_status
after_status
reason
target_context_id
write_result
candidate snapshots, unless omitted
```

Use `--audit-without-candidates` when the report should contain only the decision
summary and write result.

The audit file is local only. It prepares future projection/reconciliation work
without introducing an external API.
