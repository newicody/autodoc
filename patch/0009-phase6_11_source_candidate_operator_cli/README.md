# 0009 — Phase 6.11 SourceCandidate Operator Command Surface

This patch adds a unified local SourceCandidate operator CLI.

It is adapter-only and delegates to existing command-specific CLIs:

- intake
- review
- decide
- review-audit
- report
- report-file
- bundle

No business logic, backend, Scheduler modification or external integration is added.
