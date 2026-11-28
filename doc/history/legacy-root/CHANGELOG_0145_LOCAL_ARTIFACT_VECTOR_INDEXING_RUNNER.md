# Changelog 0145 — Local artifact vector indexing runner

Added:

- `tools/run_local_artifact_vector_indexing_runner.py`
- tests for plan/result artifact envelope behavior
- rule tests preventing new orchestrator/adapter wheels
- architecture docs, code-rule addendum, DOT graph, manifest, and test report

0145 reuses the existing Scheduler vector indexing smoke and writes local artifact input/report files under `.var/smoke` by default.
