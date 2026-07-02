# Phase 6.11 — SourceCandidate Operator Command Surface

Phase 6.11 introduces a single local command surface for the SourceCandidate operator workflow.

Example:

```bash
PYTHONPATH=src python -m context.source_candidate_operator_cli review \
  --store-file /tmp/source_candidates.json \
  --format text
```

The command is a dispatcher only. Existing specialized CLIs remain available and are delegated to unchanged.

Supported subcommands:

```text
intake
review
decide
review-audit
report
report-file
bundle
```

No external service is contacted.
