# Phase 6.3 — Hardware observation contracts

## Intention
Introduce immutable, versioned contracts for OS hardware observations and their read-only projection alongside Scheduler resource inventory.

## Scope
- Add `HardwareSample`, typed metrics and collection errors.
- Add `HardwareCell` with distinct physical and Scheduler snapshots.
- Add strict validation and mapping serialization.
- Add focused contract tests.

## Explicit boundaries
- Keep `missipy.cell.v1` unchanged.
- Do not modify Scheduler, EventBus, runtime 0287, startup or OpenRC.
- Do not add an OS collector or poller.
- Do not infer Scheduler capacity from physical utilization.
- Unknown values remain unknown; they are never represented as zero.

## Validation
Expected local command:
```sh
pytest -q tests/contracts/test_hardware.py
```
Validation exécutée sur le checkout local : 18 tests passés (`tests/contracts/test_hardware.py` et `tests/contracts/`).

## Phase review
```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: immutable stdlib-only contracts; no new IO boundary or runtime technique
live_path_status: n/a
live_path_uses_real_backend: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
