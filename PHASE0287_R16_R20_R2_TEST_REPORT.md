# Rapport de test — 0287 r16-r20-r2

## Unité

`generer-configuration-scan-artifacts-dediee`

## Portée

- séparation ProjectV2 query-only / scan Actions;
- alignement strict project/fetch;
- surface scan live canonique;
- prévisualisation sans écriture;
- écriture locale atomique explicite;
- relecture et validation par le contrat existant;
- aucun accès distant ou secret.

## Vérifications du bundle

- syntaxe AST : réussie;
- frontières statiques : réussies;
- `git apply --check` avec README r16-r20 : réussi;
- `git diff --check` : réussi;
- aucun cache Python inclus.

La suite complète est exécutée par `apply_patch_queue.py`.
