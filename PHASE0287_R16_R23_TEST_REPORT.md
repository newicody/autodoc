# Rapport de test — 0287 r16-r23

## Unité

`valider-triplet-fetche-avant-intake`

## Portée

- sélection d’un run explicite;
- exactement un `ready_run`;
- chargement local borné des trois rôles;
- réutilisation de l’assemblage dual-artifact;
- réutilisation de la validation des digests;
- réutilisation du work package corrélé;
- réutilisation de l’admissibilité;
- verrou `Recherche/initial`;
- route candidate non exécutée;
- digest local de validation;
- aucune modification du workflow ou des artefacts Actions;
- aucune mutation GitHub, SQL, Qdrant ou Scheduler.

## Vérifications du bundle

- syntaxe AST du script et des tests : réussie;
- tests ciblés avec stubs des contrats existants : réussis;
- contrôle statique des frontières : réussi;
- `git apply --check` sur arbre propre : réussi;
- `git diff --check` : réussi;
- README cumulatif non modifié;
- aucun cache Python inclus.

La suite complète est exécutée par `apply_patch_queue.py`.
