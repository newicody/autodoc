# Rapport de test — 0287 r16-r20-r8

## Unité

`selectionner-triplet-artifacts-explicite`

## Portée

- sélection exacte de trois artefacts;
- validation des rôles human-readable;
- refus des identifiants mélangés;
- refus des autres causes de report;
- résolution unique des répertoires de staging;
- lecture bornée des trois fichiers;
- compatibilité avec le chargeur `ready_run` existant;
- absence de politique automatique « latest ».

## Vérifications du bundle

- syntaxe AST : réussie;
- frontières statiques : réussies;
- `git apply --check` sur arbre propre : réussi;
- `git diff --check` : réussi;
- README cumulatif non modifié;
- aucun cache Python inclus.

La suite complète est exécutée par `apply_patch_queue.py`.
