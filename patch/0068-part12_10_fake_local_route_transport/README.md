# 0068-part12_10_fake_local_route_transport

Phase 0068 : fake local route transport.

## Objectif

Simuler le runtime local sans vrai `/dev/shm` :

```text
<runtime_root>/
  data.index.jsonl
  event.bus.jsonl
  context.bus.jsonl
  routes/<route_id>/messages.jsonl
```

Cela permet de tester :

```text
baby_fork_report.json
-> runtime projection
-> fake data.index
-> fake event.bus
-> fake context.bus
-> fake routes/*
```

## Ajouts

- `src/runtime/fake_route_transport.py`
- `tools/write_baby_fork_fake_runtime.py`
- `doc/architecture/FAKE_LOCAL_ROUTE_TRANSPORT.md`
- `doc/changelog/0068-fake-local-route-transport.md`
- `tests/test_fake_route_transport.py`
- `tests/rules/test_fake_local_route_transport_rule.py`

## Non-objectifs

- Pas de vrai `/dev/shm`.
- Pas de semaphores.
- Pas de ring buffer.
- Pas de eventfd/futex.
- Pas de RouteProxy daemon.
- Pas de ControlFS watcher.
- Pas de wiring Scheduler.
- Pas de NetworkBridge.
- Pas de HardwareBridge.
- Pas de cluster.

## Prerequis

Appliquer avant :

```text
0063-r2-part12_5_controlfs_manifest_schema_validator
0064-part12_6_routeproxy_dry_run_reconciler
0065-part12_7_shm_runtime_message_schemas
0066-part12_8_baby_fork_runtime_message_projection
0067-part12_9_baby_fork_projection_report_compat
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0068-part12_10_fake_local_route_transport

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate conseillee

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_fake_route_transport.py \
  tests/test_baby_fork_runtime_projection.py \
  tests/test_baby_fork_runtime_projection_compat.py

PYTHONPATH=src:. pytest -q tests/rules
```

## CLI exemple

```bash
PYTHONPATH=src:. python tools/write_baby_fork_fake_runtime.py \
  .var/baby_fork_smoke/baby_fork_report.json \
  .var/baby_fork_fake_runtime
```

Puis :

```bash
find .var/baby_fork_fake_runtime -type f | sort
cat .var/baby_fork_fake_runtime/event.bus.jsonl
```

## Prochaine phase recommandee

0069 : ingestion Recorder depuis fake runtime messages ou emission optionnelle de cette surface depuis le CLI baby-fork.
