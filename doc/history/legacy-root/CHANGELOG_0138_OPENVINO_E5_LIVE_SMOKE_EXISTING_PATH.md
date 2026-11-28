# Changelog 0138 — OpenVINO/E5 live smoke existing path

Added an operator smoke command that plans or executes OpenVINO/E5 through existing surfaces only.

Added:

- `tools/run_openvino_e5_live_smoke.py`
- `tests/tools/test_openvino_e5_live_smoke_existing_path_0138.py`
- `tests/rules/test_openvino_e5_live_smoke_existing_path_0138_rule.py`
- `doc/architecture/OPENVINO_E5_LIVE_SMOKE_EXISTING_PATH_0138.md`
- `doc/code-rules/0138_openvino_e5_live_smoke_existing_path_rule.md`
- `doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0138.md`
- `doc/docs/architecture/runtime/138_openvino_e5_live_smoke_existing_path.dot`
- `doc/manifests/MANIFEST_0138_CHANGED_FILES.md`
- `PHASE0138_TEST_REPORT.md`

No OpenVINO import, Qdrant import, Scheduler runner, RouteProxy worker, daemon, or new embedding adapter was added.
