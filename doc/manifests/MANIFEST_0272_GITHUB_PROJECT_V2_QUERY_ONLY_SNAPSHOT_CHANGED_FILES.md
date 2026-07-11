# Manifest — 0272-r3 GitHub ProjectV2 query-only snapshot

## Added

- `src/context/github_project_v2_query_only_snapshot_0272.py`
- `tools/run_github_project_v2_query_only_snapshot_0272.py`
- `config/github_project_v2_query_only.example.ini`
- `tests/context/test_github_project_v2_query_only_snapshot_0272.py`
- `tests/tools/test_run_github_project_v2_query_only_snapshot_0272.py`
- `tests/rules/test_github_project_v2_query_only_snapshot_0272_rule.py`
- `doc/architecture/GITHUB_PROJECT_V2_QUERY_ONLY_SNAPSHOT_0272.md`
- `doc/code-rules/0272_github_project_v2_query_only_snapshot_rule.md`
- `doc/docs/architecture/runtime/272_github_project_v2_query_only_snapshot.dot`
- `doc/CHANGELOG_0272_GITHUB_PROJECT_V2_QUERY_ONLY_SNAPSHOT.md`
- `doc/manifests/MANIFEST_0272_GITHUB_PROJECT_V2_QUERY_ONLY_SNAPSHOT_CHANGED_FILES.md`
- `PHASE0272_GITHUB_PROJECT_V2_QUERY_ONLY_SNAPSHOT_TEST_REPORT.md`

## Modified

- `doc/architecture/GITHUB_ACTIONS_ARTIFACT_SCAN_ONCE_LIVE_0272.md`
- `doc/code-rules/0272_github_actions_artifact_scan_once_live_rule.md`

## Explicitly unchanged

- the 0272-r2 GitHub Actions artifact fetch implementation;
- 0267 local GitHub handoff;
- remote mutation gate;
- Scheduler and its loop;
- SQL, Qdrant, OpenVINO, EventBus, PassiveSupervisor, SHM, RouteProxy and ControlProxy.
