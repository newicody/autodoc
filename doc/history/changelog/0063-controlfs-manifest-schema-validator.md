# 0063 - ControlFS manifest schema and validator

## Added

- `runtime.controlfs_manifest` parser and validator.
- `RouteManifest` dataclass.
- Route ID normalization and path-safe validation.
- Helper to resolve `desired/routes/<route_id>/manifest.json`.
- CLI tool `tools/validate_controlfs_manifest.py`.
- ControlFS manifest schema documentation.
- Functional tests for valid and invalid manifests.
- Rule tests ensuring this phase does not introduce shm, RouteProxy daemon, network or hardware behavior.

## Not added

- No Scheduler wiring.
- No real ControlFS daemon.
- No RouteProxy implementation.
- No shm/semaphore implementation.
- No NetworkBridge.
- No HardwareBridge.
- No cluster dispatch.
