# Phase 0277 test report

Scope: optional GitHub Copilot advisory authentication, failure semantics, and
real-Issue authoritative request validation.

Validation commands:

```bash
PYTHONPATH=src:. python -m compileall -q templates/github/scripts tests/tools
PYTHONPATH=src:. pytest -q \
  tests/rules/test_github_dual_artifact_actions_workflow_0275_rule.py \
  tests/tools/test_github_copilot_advisory_optional_0277.py
PYTHONPATH=src:. pytest -q tests/rules
```

Focused coverage:

- ephemeral `GITHUB_TOKEN` authentication;
- scoped `copilot-requests: write` permission;
- non-blocking CLI failure and invalid response;
- stale advisory removal;
- explicit required-mode failure;
- successful non-authoritative advisory generation;
- rejection of a missing Issue envelope;
- acceptance of a valid title-only Issue.
