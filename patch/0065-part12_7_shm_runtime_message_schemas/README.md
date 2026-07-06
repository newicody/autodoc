# 0065-part12_7_shm_runtime_message_schemas

Phase 0065 / P3 : schemas du SHM Runtime.

## Objectif

Definir les structures compactes avant tout vrai transport :

```text
event.bus
context.bus
data.index / DataHandle
routes/<route_id> message
```

## Ajouts

- `src/runtime/shm_runtime_schema.py`
- `tools/validate_shm_runtime_message.py`
- `doc/architecture/SHM_RUNTIME_MESSAGE_SCHEMAS.md`
- `doc/changelog/0065-shm-runtime-message-schemas.md`
- `tests/test_shm_runtime_schema.py`
- `tests/rules/test_shm_runtime_message_schemas_rule.py`

## Non-objectifs

- Pas de vrai `/dev/shm`.
- Pas de semaphores.
- Pas de ring buffer.
- Pas de daemon RouteProxy.
- Pas de wiring Scheduler.
- Pas de NetworkBridge.
- Pas de HardwareBridge.
- Pas de cluster.

## Prerequis

Appliquer avant :

```text
0063-r2-part12_5_controlfs_manifest_schema_validator
0064-part12_6_routeproxy_dry_run_reconciler
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0065-part12_7_shm_runtime_message_schemas

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate conseillee

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q   tests/test_controlfs_manifest.py   tests/test_routeproxy_reconciler.py   tests/test_shm_runtime_schema.py

PYTHONPATH=src:. pytest -q   tests/rules/test_controlfs_manifest_schema_rule.py   tests/rules/test_routeproxy_dry_run_reconciler_rule.py   tests/rules/test_shm_runtime_message_schemas_rule.py

PYTHONPATH=src:. pytest -q tests/rules
```

## CLI exemple

```bash
PYTHONPATH=src:. python tools/validate_shm_runtime_message.py message.json
```

## Prochaine phase recommandee

0066 / P4 : brancher le vocabulaire `route_id`, `event message`, `context message` et `data_handle` dans le smoke project baby-fork.
