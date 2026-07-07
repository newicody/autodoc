# Phase 0167 test report — GitHub artifact server dataset sync

## Target tests

```text
PYTHONPATH=src:. pytest -q tests/context/test_github_artifact_server_dataset_0167.py tests/tools/test_github_artifact_server_sync_once_0167.py tests/rules/test_github_artifact_server_dataset_sync_0167_rule.py
```

## Expected behavior

- fetched local artifact directory is copied into configured server dataset
- attachments are detected by kind
- conversion queue is written after raw sync
- VisPy observation event is written
- no GitHub API call
- no user artifacts are stored in Git
