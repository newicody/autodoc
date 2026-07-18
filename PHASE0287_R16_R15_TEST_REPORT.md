# Rapport de test — 0287 r16-r15

## Unité

`construire-synthese-liaison-des-deux-analyses`

## Portée

- validation SHA-256 des deux corps SQL réhydratés;
- reconnaissance des schémas des deux spécialistes;
- validation de la filiation de la seconde analyse;
- mutualisation locale des preuves;
- construction de deux fragments profonds et d’un fragment d’audit;
- réutilisation de la synthèse de liaison existante;
- aucune publication, persistance, projection ou inférence.

## Vérifications du bundle

- compilation Python : réussie;
- contrôle statique des frontières : réussi;
- `git apply --check` sur une base vide : réussi;
- `git diff --check` : réussi.

La suite complète `tests/rules` est exécutée par `apply_patch_queue.py`.
