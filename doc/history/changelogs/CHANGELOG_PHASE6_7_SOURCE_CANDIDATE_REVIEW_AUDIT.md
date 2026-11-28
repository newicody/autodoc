# Phase 6.7 — SourceCandidate Review Audit Summary

## Added

- Added `src/context/source_candidate_review_audit.py` as a pure local projection layer over an existing `SourceCandidateReviewResult`.
- Added `src/context/source_candidate_review_audit_cli.py`, reusing the existing review Scheduler live path before enriching the result with local audit summaries.
- Added tests for stored decision summaries, audit file summaries, missing audit files, and CLI JSON output.
- Added rule tests to keep the feature local-only and tied to the existing review live path.
- Added architecture DOT for the review audit projection.

## Boundaries

- No network.
- No external backend.
- No automatic decision.
- No Scheduler modification.
- No write to the SourceCandidate store.
