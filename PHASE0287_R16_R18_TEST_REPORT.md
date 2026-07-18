# Rapport de test — 0287 r16-r18

## Unité

`enregistrer-preuve-publication-et-clore-cycle`

## Portée

- validation du livrable SQL r16-r16;
- validation du résultat distant r16-r17;
- exigence d’un mode execute complet;
- exigence d’un readback exact valide;
- création d’un objet et artefact de preuve;
- création d’une révision enfant `cycle_status=closed`;
- writes SQL idempotents et relecture exacte;
- aucune nouvelle mutation GitHub ou ProjectV2.

## Vérifications du bundle

- analyse syntaxique AST : réussie;
- contrôle statique des frontières : réussi;
- `git apply --check` sur une base vide : réussi;
- `git diff --check` : réussi;
- aucun `__pycache__` ou fichier `.pyc` inclus.

La suite complète `tests/rules` est exécutée par `apply_patch_queue.py`.
