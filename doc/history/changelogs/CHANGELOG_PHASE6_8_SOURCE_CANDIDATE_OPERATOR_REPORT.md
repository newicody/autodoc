# Changelog — Phase 6.8 SourceCandidate Operator Report CLI

## Added

- `SourceCandidateOperatorReportPolicy`
- `SourceCandidateOperatorReportItem`
- `SourceCandidateOperatorReportResult`
- `build_source_candidate_operator_report()`
- `source_candidate_operator_report_cli.py`
- deterministic JSON and text report rendering
- rule tests for additive projection and no external backend dependency

## Behavior

The operator report summarizes a review-audit result with:

- status counts
- decision counts
- actionable/terminal counts
- audit presence counts
- bounded next-action list

## Out of scope

- no external API
- no vector database
- no model inference
- no Scheduler modification
- no automatic decision
