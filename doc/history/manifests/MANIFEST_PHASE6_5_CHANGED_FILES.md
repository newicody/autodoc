# Phase 6.5 Changed Files

- `src/contracts/event.py` — add SourceCandidate decision event types.
- `src/context/source_candidate_decision.py` — local decision command/result/use-case.
- `src/context/source_candidate_decision_cli.py` — CLI adapter through Scheduler.
- `src/context/source_candidate_decision_handlers.py` — decision handler and typed result extractor.
- `tests/context/test_source_candidate_decision.py` — pure use-case tests.
- `tests/context/test_source_candidate_decision_live_path.py` — Scheduler live-path test.
- `tests/context/test_source_candidate_decision_cli.py` — CLI adapter tests.
- `tests/rules/test_source_candidate_decision_live_path_rule.py` — rule tests.
- `doc/docs/architecture/context/46_source_candidate_decision_live_path.dot` — architecture graph source.
- `doc/changelogs/CHANGELOG_PHASE6_5_SOURCE_CANDIDATE_DECISION.md` — changelog.
- `doc/code-rules/PHASE6_5_CODE_RULE_ALIGNMENT.md` — code rule alignment.
- `doc/releases/README_PHASE6_5_SOURCE_CANDIDATE_DECISION.md` — release README.
- `doc/reports/phase6/PHASE6_5_TEST_REPORT.md` — test report.

No generated `.svg` files are versioned.
No `.pyo` files are versioned.
No network, GitHub API, Qdrant, LLM or OpenVINO dependency is added.
