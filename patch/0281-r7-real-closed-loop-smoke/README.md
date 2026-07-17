# 0281-r7-real-closed-loop-smoke

This archive replaces the rejected manual-download version.

```text
autodoc: change required
projects: no change required
projects_repository_change_required: false
existing_server_dataset_reused: true
```

```bash
PYTHONPATH=src:. python   tools/run_github_real_closed_loop_smoke_0281.py   --config .var/config/github_artifact_server_fetch.ini   --run-id <RUN_ID>   --issue-number <ISSUE_NUMBER>   --format json
```
