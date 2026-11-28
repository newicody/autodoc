# Manifest 0281-r3 — fetch-once run-group integration

Changed files:

- `tools/run_github_dual_artifact_server_sync_once_0281.py`
- `tests/tools/test_github_dual_artifact_server_sync_once_0281.py`
- `tests/rules/test_github_dual_artifact_fetch_run_group_integration_0281_rule.py`
- `doc/architecture/GITHUB_DUAL_ARTIFACT_FETCH_RUN_GROUP_INTEGRATION_0281.md`
- `doc/manifests/MANIFEST_0281_R3_FETCH_ONCE_RUN_GROUP_INTEGRATION.md`
- `PHASE0281_R3_FETCH_ONCE_RUN_GROUP_INTEGRATION_REPORT.md`

Repository impact:

```text
newicody/autodoc: change required
newicody/projects: no change required
projects_repository_change_required: false
```

Operational selection:

```text
--sync-tool tools/run_github_dual_artifact_server_sync_once_0281.py
```

The patch adds no dependency, network client, GitHub mutation, SQL write,
Qdrant write, Scheduler modification or parallel fetcher.
