# Phase 0278 test report

Scope: controlled GitHub workflow event-path boundary.

Validation commands:

```bash
PYTHONPATH=src:. python -m compileall -q templates/github/scripts tests/tools
PYTHONPATH=src:. pytest -q \
  tests/rules/test_github_dual_artifact_actions_workflow_0275_rule.py \
  tests/tools/test_github_copilot_advisory_optional_0277.py
```

Focused coverage:

- controlled workflow uses `AUTODOC_EVENT_PATH`;
- native `GITHUB_EVENT_PATH` remains a fallback;
- an explicit controlled event wins when both paths exist;
- the authoritative builder still rejects a missing Issue envelope.
