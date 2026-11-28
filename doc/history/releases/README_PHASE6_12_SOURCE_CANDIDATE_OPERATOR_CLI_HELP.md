# Phase 6.12 — SourceCandidate Operator CLI Help Gate

This phase adds a small stability gate for the unified SourceCandidate operator CLI.

The goal is to make sure the consolidated command surface remains discoverable and adapter-only.

## Command surface guarded

```bash
PYTHONPATH=src python -m context.source_candidate_operator_cli --help
```

Expected commands include:

```text
intake
review
decide
review-audit
report
report-file
bundle
```

## Scope

This is not a new business capability. It is a regression and documentation phase.
