# Manifest — 0272-r7 ProjectV2 SourceCandidate operator gate

## Modified

- `README.md`
- `config/github_project_v2_query_only.example.ini`
- `src/context/github_project_system_deployment_readiness_0272.py`
- `tools/run_github_project_system_deployment_readiness_0272.py`
- `doc/operator/GITHUB_PROJECT_ACTIONS_CONFIGURATION_0272.md`
- `doc/docs/architecture/00_global.dot`
- `tests/context/test_github_project_system_deployment_readiness_0272.py`
- `tests/tools/test_run_github_project_system_deployment_readiness_0272.py`

## Added

- `src/context/github_project_v2_source_candidate_gate_0272.py`
- `tools/gate_github_project_v2_source_candidate_0272.py`
- `tests/context/test_github_project_v2_source_candidate_gate_0272.py`
- `tests/tools/test_gate_github_project_v2_source_candidate_0272.py`
- `tests/rules/test_github_project_v2_source_candidate_gate_0272_rule.py`
- `doc/architecture/GITHUB_PROJECT_V2_SOURCE_CANDIDATE_GATE_0272.md`
- `doc/code-rules/0272_github_project_v2_source_candidate_gate_rule.md`
- `doc/CHANGELOG_0272_GITHUB_PROJECT_V2_SOURCE_CANDIDATE_GATE.md`
- `doc/releases/0272-r7-github-project-v2-source-candidate-operator-gate.md`
- `doc/docs/architecture/runtime/272_github_project_v2_source_candidate_gate.dot`
- `PHASE0272_GITHUB_PROJECT_V2_SOURCE_CANDIDATE_GATE_TEST_REPORT.md`

## Explicitly unchanged

- `src/scheduler.py`
- `Scheduler.run()`
- SQL store implementations
- Qdrant projection/recall implementations
- SHM, RouteProxy and ControlProxy
