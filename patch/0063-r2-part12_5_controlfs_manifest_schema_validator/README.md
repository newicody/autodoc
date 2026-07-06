# 0063-r2-part12_5_controlfs_manifest_schema_validator

Version r2 de 0063.

Différence avec 0063 initial :
- ne crée plus `src/runtime/__init__.py`, car ce fichier existe déjà dans ton dépôt.

## Objectif

Rendre exécutable la première couche ControlFS sans modifier le Scheduler et sans créer de vrai shm.

Ajoute :

- `runtime.controlfs_manifest.RouteManifest`
- validation de `missipy.controlfs.route_manifest.v1`
- validation stricte de `route_id`
- helper `desired/routes/<route_id>/manifest.json`
- outil CLI `tools/validate_controlfs_manifest.py`
- documentation `CONTROLFS_MANIFEST_SCHEMA.md`
- tests fonctionnels + règles documentaires

## Non-objectifs

- Pas de daemon RouteProxy.
- Pas de vrai `/dev/shm`.
- Pas de sémaphores.
- Pas de NetworkBridge.
- Pas de HardwareBridge.
- Pas de refactor Scheduler.
- Pas de cluster.

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0063-r2-part12_5_controlfs_manifest_schema_validator

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate conseillée

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/test_controlfs_manifest.py
PYTHONPATH=src:. pytest -q tests/rules/test_controlfs_manifest_schema_rule.py
PYTHONPATH=src:. pytest -q tests/rules
```

## Prochaine phase recommandée

0064 / P2 : `RouteProxy dry-run reconciler`

- lit `desired/routes/*`
- lit `active/routes/*`
- produit un plan create/delete/update
- ignore les manifests invalides
- ne crée toujours pas de vrai shm
