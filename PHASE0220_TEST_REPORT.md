# Phase 0220 Test Report

Patch: `0220-passive_bus_supervisor_cellular_snapshot`

## Purpose

Resume the passive bus supervisor work by adding a stdlib-only cellular snapshot
contract and CLI builder. The snapshot makes future GitHub artifact, fetch,
SourceCandidate, SQL/Qdrant, pushback, proxy, SHM, and policy events visible
without giving the supervisor runtime authority.

## Expected Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_passive_bus_supervisor_cellular_snapshot_0220.py \
  tests/tools/test_run_passive_bus_supervisor_cellular_snapshot_0220.py \
  tests/rules/test_passive_bus_supervisor_cellular_snapshot_0220_rule.py
PYTHONPATH=src:. python -m pytest -q tests/rules
```

## Manual Smoke

```bash
mkdir -p .var/autodoc/runtime/dev-controlled/supervision
cat > .var/autodoc/runtime/dev-controlled/supervision/events.jsonl <<'JSONL'
{"event_id":"evt-1","event_kind":"scheduler_tick","cell_id":"scheduler","cell_kind":"SCHEDULER","state":"running","observed_at":"2026-07-08T00:00:00Z"}
{"event_id":"evt-2","event_kind":"policy_blocked","cell_id":"policy","cell_kind":"POLICY_GATE","state":"blocked","observed_at":"2026-07-08T00:00:01Z","policy_decision_id":"policy-1","error":"write denied"}
JSONL
PYTHONPATH=src:. python tools/run_passive_bus_supervisor_cellular_snapshot_0220.py \
  --events-jsonl .var/autodoc/runtime/dev-controlled/supervision/events.jsonl \
  --output .var/autodoc/runtime/dev-controlled/supervision/snapshot.json \
  --format json
```

## Sandbox Result

Not run here against the real repository because the current sandbox does not
contain the Autodoc checkout and local GitHub clone is blocked. The patch is
additive and must be validated through `apply_patch_queue.py` in the real repo.

## Non-Stdlib Dependencies

None.

## 0220-r1 Follow-Up

The first real repository run found one subprocess-only failure in
`tests/tools/test_run_passive_bus_supervisor_cellular_snapshot_0220.py`: direct
execution of the CLI could not reliably import `src.context...` because Python
starts with `tools/` on `sys.path`. Patch `0220-r1` adds the repository root to
`sys.path` before project imports.
