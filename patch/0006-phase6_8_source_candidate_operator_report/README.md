# 0006 — Phase 6.8 SourceCandidate Operator Report CLI

This patch adds a deterministic local operator report over the Phase 6.7 SourceCandidate review-audit summary.

## Scope

- summarize status counts
- summarize decision counts
- count actionable and terminal candidates
- count audit coverage
- expose bounded next actions
- render text and JSON

## Out of scope

- external API integration
- vector database
- model inference
- Scheduler modification
- automatic decisions
