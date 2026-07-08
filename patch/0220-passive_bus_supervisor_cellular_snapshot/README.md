# 0220 - Passive Bus Supervisor Cellular Snapshot

This patch resumes the existing passive bus supervision direction without adding
a parallel runtime authority.

It adds:

- `src/context/passive_bus_supervisor_cellular_snapshot.py`
- `tools/run_passive_bus_supervisor_cellular_snapshot_0220.py`
- focused tests
- a code-rule guard
- architecture docs, changelog, manifest, and DOT graph

The implementation is stdlib-only and observation-only. It does not call
`Scheduler.run`, GitHub, SQL, Qdrant, VisPy, proxy control surfaces, or network
APIs.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0220-passive_bus_supervisor_cellular_snapshot \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0220-passive_bus_supervisor_cellular_snapshot \
  --commit \
  --push \
  --allow-dirty
```

## Validate

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
