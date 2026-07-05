# Manifest — 0102 ControlProxy existing paths audit

## Added files

```text
PHASE0102_TEST_REPORT.md
doc/CHANGELOG_0102_CONTROLPROXY_EXISTING_PATHS_AUDIT.md
doc/architecture/CONTROLPROXY_EXISTING_PATHS_AUDIT_0102.md
doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0102.md
doc/docs/architecture/runtime/92_controlproxy_existing_paths_audit.dot
doc/manifests/MANIFEST_0102_CHANGED_FILES.md
tests/rules/test_controlproxy_existing_paths_audit_0102_rule.py
```

## Intent

0102 is audit and marking only. It classifies the existing paths so 0103 can introduce `RouteRuntimeManager` without creating a scheduler-like ControlProxy coordinator.

## Non-changes

```text
No runtime code.
No CLI.
No daemon/service/OpenRC.
No resident watcher.
No kernel-loop modification.
No queue modification.
No dispatcher implementation modification.
No policy implementation modification.
No EventBus implementation modification.
No new bus.
No ControlProxyRouteCoordinator scheduler-like.
No RouteRuntimeManager implementation yet.
No Qdrant / LLM / OpenVINO / NetworkBridge / HardwareBridge path.
```
