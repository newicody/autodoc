# Rapport de test — 0287 r16-r20-r4

## Unité

`cabler-resolution-projectv2-dans-prepare`

## Portée

- bundle cumulatif incluant le résolveur r3 absent du master;
- résolution Issue/ProjectV2/champ avant acquisition du runtime;
- suppression des identifiants ProjectV2 obligatoires en CLI;
- overrides couplés et contrôlés par readback;
- propagation exacte au plan de publication;
- persistance de la cible dans `prepared.json`;
- blocage précoce sans SQL/Qdrant/Scheduler en cas d’échec.

## Vérifications du bundle

- syntaxe AST : réussie;
- frontières statiques : réussies;
- `git apply --check` contre les fichiers r16-r20-r1 complets : réussi;
- `git diff --check` : réussi;
- README cumulatif non modifié;
- aucun cache Python inclus.

La suite complète est exécutée par `apply_patch_queue.py`.
