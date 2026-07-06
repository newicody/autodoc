# 0078-part12_17_inprocess_frame_ring_integration

Phase 0078 : integration frame codec + ring in-process.

## Objectif

Tester :

```text
RouteMessage
-> frame binaire
-> ring in-process borne
-> drain
-> decode
-> RouteMessage valide
```

## Ajouts

- `src/runtime/inprocess_frame_ring.py`
- `tools/replay_fake_routes_to_frame_ring.py`
- `doc/architecture/INPROCESS_FRAME_RING_INTEGRATION.md`
- `doc/changelog/0078-inprocess-frame-ring-integration.md`
- `tests/test_inprocess_frame_ring.py`
- `tests/rules/test_inprocess_frame_ring_integration_rule.py`

## Stats ajoutees

```text
capacity
occupancy
total_frame_bytes
max_frame_bytes
write_sequence
read_sequence
dropped_count
overflow_policy
```

## Non-objectifs

- Pas de vrai `/dev/shm`.
- Pas de mmap.
- Pas de semaphores.
- Pas de eventfd/futex.
- Pas de RouteProxy daemon.
- Pas de watcher ControlFS.
- Pas de wiring Scheduler.
- Pas de zero-copy.
- Pas de thread/process safety.
- Pas de NetworkBridge.
- Pas de HardwareBridge.
- Pas de cluster.

## Prerequis

Appliquer avant tous les patchs jusqu'a :

```text
0077-part12_16_route_message_frame_codec
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0078-part12_17_inprocess_frame_ring_integration

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate conseillee

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_inprocess_frame_ring.py \
  tests/test_route_frame_codec.py \
  tests/test_inprocess_ring_buffer.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Test CLI apres application

Produire la fake runtime :

```bash
PYTHONPATH=src:. python tools/run_baby_fork_runtime_flow.py \
  .var/baby_fork_smoke/baby_fork_report.json \
  .var/baby_fork_fake_runtime \
  .var/baby_fork_fake_runtime/runtime_journal.jsonl \
  --controlfs-root .var/baby_fork_controlfs
```

Rejouer en frame ring :

```bash
PYTHONPATH=src:. python tools/replay_fake_routes_to_frame_ring.py \
  .var/baby_fork_fake_runtime \
  --capacity 4
```

Attendu :

```text
sent = 3
errors = []
stats.*.occupancy = 1
stats.*.total_frame_bytes > 0
```

## Prochaine phase recommandee

0079 : byte-capacity globale / fixed slot constraints, toujours sans mmap.
