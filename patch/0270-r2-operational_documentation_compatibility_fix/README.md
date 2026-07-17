# 0270-r2-operational_documentation_compatibility_fix

## Objet

Corrige les six régressions de règles révélées après l'application de
`0270-r1-operational_documentation_consolidation`, sans annuler la consolidation
0260→0269 et sans ajouter de capacité runtime.

Le correctif :

- restaure les sections contractuelles du README racine ;
- conserve le baseline opérationnel 0260→0269 dans `## Current architecture` ;
- restaure les formulations de compatibilité 0154 attendues par les règles ;
- restaure `DbApiSqlContextStore.upsert_record` et `AUTODOC_SQL_CONTEXT_DB` dans
  l'index courant ;
- remplace la graphie interdite `Scheduler.run(` par une formulation descriptive ;
- ajoute un test de non-régression 0270.

## Situation attendue avant application

`0270-r1` a déjà été appliqué dans la copie de travail, mais son commit a été
interrompu par les tests. Les modifications r1 sont donc présentes et non
commitées. Ne pas réappliquer ni annuler r1 : appliquer directement r2 avec
`--allow-dirty`.

La patch queue stage ensuite toutes les modifications suivies et nouveaux fichiers
hors `patch/` et `.var/`; le commit vert contiendra donc la consolidation r1 et sa
correction r2.

## Frontières

Ce patch reste documentation-only :

- aucun fichier `src/` ou `tools/` ;
- aucun nouveau module, handler, adapter, manager ou orchestrateur ;
- aucune modification du Scheduler ;
- aucun appel SQL, Qdrant, OpenVINO, GitHub ou OpenRC ;
- aucune dépendance non-stdlib.

## Application

```bash
cd /home/eric/projet/git/autodoc

git status --short
git diff --check

tar -xJf \
  /mnt/data/0270-r2-operational_documentation_compatibility_fix.tar.xz

python apply_patch_queue.py \
  --patch 0270-r2-operational_documentation_compatibility_fix \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0270-r2-operational_documentation_compatibility_fix \
  --commit \
  --push \
  --allow-dirty
```

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

Validation ciblée pendant la construction :

```text
git apply --check: OK
root README + 0154 + 0270 focused rules: 14 passed
```
