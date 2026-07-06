# 0064-part12_6_routeproxy_dry_run_reconciler

Phase 0064 / P2 : RouteProxy dry-run reconciler.

## Objectif

Lire ControlFS sans rien matérialiser :

```text
desired/routes/*
active/routes/*
```

et produire un plan :

```text
create
delete
update
noop
error
```

## Ajouts

- `src/runtime/routeproxy_reconciler.py`
- `tools/routeproxy_dry_run.py`
- `doc/architecture/ROUTEPROXY_DRY_RUN_RECONCILER.md`
- `doc/changelog/0064-routeproxy-dry-run-reconciler.md`
- `tests/test_routeproxy_reconciler.py`
- `tests/rules/test_routeproxy_dry_run_reconciler_rule.py`

## Non-objectifs

- Pas de RouteProxy daemon.
- Pas de inotify.
- Pas de vrai `/dev/shm`.
- Pas de sémaphores.
- Pas de wiring Scheduler.
- Pas de NetworkBridge.
- Pas de HardwareBridge.
- Pas de cluster.

## Prérequis

Appliquer d'abord `0063-r2-part12_5_controlfs_manifest_schema_validator`.

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0064-part12_6_routeproxy_dry_run_reconciler

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate conseillée

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/test_controlfs_manifest.py tests/test_routeproxy_reconciler.py
PYTHONPATH=src:. pytest -q tests/rules/test_controlfs_manifest_schema_rule.py tests/rules/test_routeproxy_dry_run_reconciler_rule.py
PYTHONPATH=src:. pytest -q tests/rules
```

## CLI exemple

```bash
PYTHONPATH=src:. python tools/routeproxy_dry_run.py /run/autodoc/controlfs --summary
```

## Prochaine phase recommandée

0065 / P3 : schémas `event.bus`, `context.bus`, `data.index` et `DataHandle`.
