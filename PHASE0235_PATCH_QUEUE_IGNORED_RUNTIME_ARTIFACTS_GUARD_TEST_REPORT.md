# Phase 0235 test report — patch queue ignored runtime artifacts guard

## Intent

Prevent ignored runtime artifacts under `.var/` from being selected by
`changed_files_for_commit()` and passed to `git add`.

## Expected validation

```text
python -m compileall -q apply_patch_queue.py tests
python -m pytest -q tests/tools/test_patch_queue_ignored_runtime_artifacts_0235.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Boundary

This patch changes patch queue commit selection only. It does not modify
Scheduler, EventBus, PassiveSupervisorSink, proxy, SHM, SQL, Qdrant, or GitHub runtime behavior.
