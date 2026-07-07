# Phase 0165 test report — project push frame and fcron ConfigObj

## Target tests

```text
PYTHONPATH=src:. pytest -q tests/context/test_github_project_push_frame_config_0165.py tests/tools/test_github_project_push_frame_config_check_0165.py tests/rules/test_github_project_push_frame_fcron_config_0165_rule.py
```

## Target config check

```text
python tools/run_github_project_push_frame_config_check.py --config config/github_project_push_frame.example.ini --format json
```

## Expected behavior

```text
status: ok
scan mode: fcron
interval: 10 minutes
fcron table candidate written
started_fcron: false
openrc_touched: false
idempotent: true
```

## Boundary

0165 does not call GitHub, does not start fcron, does not manage OpenRC, does not
write SQL/Qdrant, and does not run Scheduler/LLM/OpenVINO.
