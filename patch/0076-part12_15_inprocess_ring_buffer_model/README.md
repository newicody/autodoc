# 0076-part12_15_inprocess_ring_buffer_model

Phase 0076 : modele ring buffer in-process, sans mmap.

## Objectif

Tester les regles du futur ring buffer avant tout IPC noyau :

```text
capacity bornee
FIFO
sequence monotone
overflow explicite
pas de silent overwrite
RouteMessage valide a la frontiere
```

## Ajouts

- `src/runtime/inprocess_ring_buffer.py`
- `tools/replay_fake_routes_to_ring.py`
- `doc/architecture/INPROCESS_RING_BUFFER_MODEL.md`
- `doc/changelog/0076-inprocess-ring-buffer-model.md`
- `tests/test_inprocess_ring_buffer.py`
- `tests/rules/test_inprocess_ring_buffer_model_rule.py`

## Overflow policies

```text
reject
drop_oldest
```

## Non-objectifs

- Pas de vrai `/dev/shm`.
- Pas de mmap.
- Pas de semaphores.
- Pas de eventfd/futex.
- Pas de RouteProxy daemon.
- Pas de watcher ControlFS.
- Pas de wiring Scheduler.
- Pas de thread/process safety.
- Pas de NetworkBridge.
- Pas de HardwareBridge.
- Pas de cluster.

## Prerequis

Appliquer avant tous les patchs jusqu'a :

```text
0075-part12_14_fake_runtime_replace_semantics
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0076-part12_15_inprocess_ring_buffer_model

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate conseillee

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_inprocess_ring_buffer.py \
  tests/test_fake_runtime_replace_semantics.py \
  tests/test_baby_fork_runtime_flow.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Test CLI apres application

D'abord produire la fake runtime :

```bash
PYTHONPATH=src:. python tools/run_baby_fork_runtime_flow.py \
  .var/baby_fork_smoke/baby_fork_report.json \
  .var/baby_fork_fake_runtime \
  .var/baby_fork_fake_runtime/runtime_journal.jsonl \
  --controlfs-root .var/baby_fork_controlfs
```

Puis rejouer les routes dans le ring in-process :

```bash
PYTHONPATH=src:. python tools/replay_fake_routes_to_ring.py \
  .var/baby_fork_fake_runtime \
  --capacity 4
```

Attendu :

```text
sent = 3
errors = []
```

## Prochaine phase recommandee

0077 : codec de frame byte-level pour RouteMessage, encore sans mmap.
