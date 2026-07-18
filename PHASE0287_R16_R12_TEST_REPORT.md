# Rapport de test — 0287 r16-r12

## Unité

`enregistrer-separement-les-deux-analyses-dans-postgresql`

## Portée

- validation des deux résultats de visite;
- création de deux objets autoritatifs distincts;
- création de deux artefacts distincts;
- création d’une révision enfant acceptée;
- inspection des collisions immuables;
- writes idempotents et relecture exacte;
- aucune projection Qdrant ni synthèse.

## Vérifications du bundle

- compilation Python : réussie;
- contrôle statique des frontières : réussi;
- `git apply --check` sur une base vide : réussi;
- `git diff --check` : réussi.

La suite complète `tests/rules` est exécutée par `apply_patch_queue.py`.
