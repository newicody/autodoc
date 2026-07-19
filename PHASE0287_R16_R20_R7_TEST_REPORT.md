# Rapport de test — 0287 r16-r20-r7

## Unité

`reutiliser-rapport-fetch-deja-pret`

## Portée

- option explicite de rapport de fetch existant;
- absence de nouveau fetch dans ce mode;
- absence d’exigence du token d’artefacts;
- maintien du token ProjectV2;
- transmission exacte au chargeur r16-r20;
- rejet d’un chemin absent;
- aucune sélection historique automatique;
- frontières et rapport opérateur explicites.

## Vérifications du bundle

- syntaxe AST : réussie;
- `git apply --check` contre r16-r20-r5 : réussi;
- `git diff --check` : réussi;
- README cumulatif non modifié;
- aucun cache Python inclus.

La suite complète est exécutée par `apply_patch_queue.py`.
