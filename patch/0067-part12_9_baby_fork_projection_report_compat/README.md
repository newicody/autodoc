# 0067-part12_9_baby_fork_projection_report_compat

Correctif de compatibilite pour la projection runtime baby-fork.

## Probleme corrige

La projection 0066 fonctionnait mais sortait sur ton vrai report :

```text
variant_count = 0
```

car les variants ne sont pas toujours dans `report["variants"]`.

## Corrections

- Extraction des variants dans plusieurs formes de rapport :
  - `variants`
  - `generated_variants`
  - `candidate_variants`
  - `variant_generator.generated_variants`
  - `variant_generator_stub.generated_variants`
  - `result.variants`
  - `final_context.variants`
  - fallback recursif
- Ajout de `variant_ids`.
- `DataHandle.hash` utilise maintenant un vrai SHA-256 deterministe du report.

## Non-objectifs

- Pas de vrai `/dev/shm`.
- Pas de semaphores.
- Pas de ring buffer.
- Pas de daemon RouteProxy.
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
0066-part12_8_baby_fork_runtime_message_projection
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0067-part12_9_baby_fork_projection_report_compat

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate conseillee

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_baby_fork_runtime_projection.py \
  tests/test_baby_fork_runtime_projection_compat.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Test CLI apres application

```bash
PYTHONPATH=src:. python tools/export_baby_fork_runtime_projection.py \
  .var/baby_fork_smoke/baby_fork_report.json | grep -A8 'variant_count'
```
