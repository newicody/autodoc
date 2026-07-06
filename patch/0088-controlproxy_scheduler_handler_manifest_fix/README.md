# 0088-controlproxy_scheduler_handler_manifest_fix

Correctif minimal du manifeste 0088.

Le premier artefact 0088 ajoutait dans `doc/manifests/MANIFEST_0088_CHANGED_FILES.md`
une section "Not changed" qui citait explicitement des chemins noyau. Le test de
règle 0088 vérifie au contraire que ces chemins sont totalement absents du
manifeste, pas seulement absents du diff fonctionnel.

## Application sur l'état après échec 0088

```bash
unzip -o /mnt/data/0088-controlproxy_scheduler_handler_manifest_fix.zip -d .
python apply_patch_queue.py --patch 0088-controlproxy_scheduler_handler_manifest_fix --allow-dirty --dry-run
python apply_patch_queue.py --patch 0088-controlproxy_scheduler_handler_manifest_fix --allow-dirty --commit --push
```

`--allow-dirty` est nécessaire uniquement parce que le patch 0088 précédent a
déjà été appliqué au working tree avant l'échec des tests.

## Scope

- Corrige uniquement le manifeste 0088.
- Ne change pas le handler.
- N'ajoute pas de CLI.
- N'ajoute pas de daemon/service/OpenRC.
- Ne touche pas au loop Scheduler.
- Ne déplace aucune décision policy/zone/scope dans ControlProxy.
