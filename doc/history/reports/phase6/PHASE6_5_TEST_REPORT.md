# Phase 6.5 Test Report — SourceCandidate Decision Live Path

Expected gate:

```bash
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src pytest -q tests/context/test_source_candidate_decision.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_decision_live_path.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_decision_cli.py
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

Expected status after local execution:

```text
source_candidate_decision: green
source_candidate_decision_live_path: green
source_candidate_decision_cli: green
rules: green
full_suite: green
```

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: New durable SourceCandidate operation follows existing live-path rule.
live_path_status: green
live_path_uses_real_backend: true
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
