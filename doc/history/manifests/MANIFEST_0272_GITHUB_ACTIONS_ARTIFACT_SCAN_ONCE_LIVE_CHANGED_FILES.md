# Manifest — 0272-r2 GitHub Actions artifact scan-once live binding

## Added

- `src/context/github_actions_artifact_scan_once_live_0272.py`
- `tools/run_github_actions_artifact_scan_once_live_0272.py`
- `tests/context/test_github_actions_artifact_scan_once_live_0272.py`
- `tests/tools/test_run_github_actions_artifact_scan_once_live_0272.py`
- `tests/rules/test_github_actions_artifact_scan_once_live_0272_rule.py`
- `doc/architecture/GITHUB_ACTIONS_ARTIFACT_SCAN_ONCE_LIVE_0272.md`
- `doc/code-rules/0272_github_actions_artifact_scan_once_live_rule.md`
- `doc/docs/architecture/runtime/272_github_actions_artifact_scan_once_live.dot`
- `doc/CHANGELOG_0272_GITHUB_ACTIONS_ARTIFACT_SCAN_ONCE_LIVE.md`
- `doc/manifests/MANIFEST_0272_GITHUB_ACTIONS_ARTIFACT_SCAN_ONCE_LIVE_CHANGED_FILES.md`
- `PHASE0272_GITHUB_ACTIONS_ARTIFACT_SCAN_ONCE_LIVE_TEST_REPORT.md`

## Modified

- `config/github_project_push_frame.example.ini`
- `templates/github/autodoc-ticket-artifact.yml`

## Explicitly unchanged

- the existing 0168 GitHub Actions GET/download client;
- the existing 0167 server dataset sync;
- 0267 local handoff;
- Scheduler and its loop;
- remote mutation gate;
- SQL, Qdrant, OpenVINO, SHM, RouteProxy and ControlProxy.
