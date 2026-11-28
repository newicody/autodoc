# Phase 6.6 Changed Files

- `src/context/source_candidate_decision.py` — add decision audit policy, audit record, atomic audit writer and `audit_path` result field.
- `src/context/source_candidate_decision_cli.py` — add `--audit-file` and `--audit-without-candidates`.
- `tests/context/test_source_candidate_decision_audit.py` — audit report and CLI tests.
- `tests/rules/test_source_candidate_decision_audit_rule.py` — repository hygiene and local-only audit rules.
- `doc/docs/architecture/context/47_source_candidate_decision_audit.dot` — architecture graph source.
- `doc/changelogs/CHANGELOG_PHASE6_6_SOURCE_CANDIDATE_DECISION_AUDIT.md` — changelog.
- `doc/code-rules/PHASE6_6_CODE_RULE_ALIGNMENT.md` — code rule alignment.
- `doc/releases/README_PHASE6_6_SOURCE_CANDIDATE_DECISION_AUDIT.md` — release README.
- `doc/reports/phase6/PHASE6_6_TEST_REPORT.md` — test report.

No generated `.svg` files are versioned.
No `.pyo` files are versioned.
No network, external API, Qdrant, LLM or OpenVINO dependency is added.
