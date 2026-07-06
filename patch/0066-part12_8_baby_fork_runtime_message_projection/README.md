# 0066-part12_8_baby_fork_runtime_message_projection

Phase 0066 / P4 : projection baby-fork vers messages runtime.

## Objectif

Brancher le vocabulaire runtime dans le smoke project baby-fork sans modifier son coeur.

Le patch ajoute un adaptateur :

```text
baby_fork_report.json
-> DataHandle
-> EventBusMessage
-> ContextBusMessage
-> RouteMessage
```

## Ajouts

- `src/context/baby_fork_runtime_projection.py`
- `tools/export_baby_fork_runtime_projection.py`
- `doc/architecture/BABY_FORK_RUNTIME_MESSAGE_PROJECTION.md`
- `doc/changelog/0066-baby-fork-runtime-message-projection.md`
- `tests/test_baby_fork_runtime_projection.py`
- `tests/rules/test_baby_fork_runtime_projection_rule.py`

## Routes baby-fork verrouillees

```text
baby_fork.retrieval
baby_fork.variant_stub
baby_fork.context_gate
```

## Non-objectifs

- Pas de changement du coeur baby-fork.
- Pas de vrai `/dev/shm`.
- Pas de semaphores.
- Pas de ring buffer.
- Pas de RouteProxy daemon.
- Pas de wiring Scheduler.
- Pas de ControlFS mutation.
- Pas de NetworkBridge.
- Pas de HardwareBridge.
- Pas de cluster.

## Prerequis

Appliquer avant :

```text
0063-r2-part12_5_controlfs_manifest_schema_validator
0064-part12_6_routeproxy_dry_run_reconciler
0065-part12_7_shm_runtime_message_schemas
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0066-part12_8_baby_fork_runtime_message_projection

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate conseillee

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_controlfs_manifest.py \
  tests/test_routeproxy_reconciler.py \
  tests/test_shm_runtime_schema.py \
  tests/test_baby_fork_runtime_projection.py

PYTHONPATH=src:. pytest -q tests/rules
```

## CLI exemple

```bash
PYTHONPATH=src:. python tools/export_baby_fork_runtime_projection.py \
  .var/baby_fork_smoke/baby_fork_report.json
```

## Prochaine phase recommandee

0067 : soit export optionnel depuis le CLI baby-fork existant, soit fake local route transport, soit recorder ingestion des messages runtime.
