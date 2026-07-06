# 0071-0073-part12_12_controlfs_babyfork_routeproxy_shm_design

Patch groupe : 0071 + 0072 + 0073.

## 0071

Ajoute les manifests ControlFS desired pour les routes baby-fork :

```text
baby_fork.retrieval
baby_fork.variant_stub
baby_fork.context_gate
```

## 0072

Lance le RouteProxy dry-run sur ces manifests.

Si `active/routes` est vide, le plan attendu contient :

```text
create baby_fork.context_gate
create baby_fork.retrieval
create baby_fork.variant_stub
```

## 0073

Ajoute le design de frontiere du futur SHM ring buffer.

Important : pas d'implementation shm dans ce patch.

## Ajouts

- `src/context/baby_fork_controlfs.py`
- `tools/write_baby_fork_controlfs_desired.py`
- `tools/baby_fork_routeproxy_plan.py`
- `doc/architecture/BABY_FORK_CONTROLFS_ROUTE_MANIFESTS.md`
- `doc/architecture/BABY_FORK_ROUTEPROXY_DRY_RUN_PLAN.md`
- `doc/architecture/SHM_RING_BUFFER_BOUNDARY_DESIGN.md`
- `doc/changelog/0071-0073-controlfs-babyfork-routeproxy-shm-design.md`
- `tests/test_baby_fork_controlfs.py`
- `tests/rules/test_baby_fork_controlfs_routeproxy_shm_design_rule.py`

## Non-objectifs

- Pas de vrai `/dev/shm`.
- Pas de mmap.
- Pas de ring buffer code.
- Pas de eventfd/futex/semaphore.
- Pas de daemon RouteProxy.
- Pas de wiring Scheduler.
- Pas de creation active/routes.
- Pas de watcher ControlFS.
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
0068-part12_10_fake_local_route_transport
0069-part12_11_fake_runtime_recorder_ingestion
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0071-0073-part12_12_controlfs_babyfork_routeproxy_shm_design

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate conseillee

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_baby_fork_controlfs.py \
  tests/test_fake_runtime_recorder.py \
  tests/test_fake_route_transport.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Test CLI

```bash
PYTHONPATH=src:. python tools/write_baby_fork_controlfs_desired.py \
  .var/baby_fork_controlfs \
  --context-id ctx-baby-fork-001

PYTHONPATH=src:. python tools/baby_fork_routeproxy_plan.py \
  .var/baby_fork_controlfs \
  --context-id ctx-baby-fork-001
```

Attendu premier run :

```text
create = 3
delete = 0
update = 0
error = 0
```

## Prochaine phase recommandee

0074 : soit option CLI baby-fork tout-en-un, soit premier modele in-process ring buffer sans mmap.
