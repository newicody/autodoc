# Rapport de test — 0287 r16-r17

## Unité

`publier-livrable-final-sur-issue-et-projectv2`

## Portée

- validation de la lignée r16-r15/r16-r16;
- adaptation vers le plan final existant;
- plan directement analysable par l’outil de publication existant;
- prévisualisation sans mutation;
- exécution avec trois verrous et digest exact;
- commentaire Issue puis champ ProjectV2;
- relecture exacte;
- rejeu idempotent;
- blocage en cas de mauvais digest;
- aucune nouvelle couche de transport.

## Vérifications du bundle

- analyse syntaxique AST : réussie;
- contrôle statique des frontières : réussi;
- `git apply --check` sur une base vide : réussi;
- `git diff --check` : réussi;
- aucun `__pycache__` ou fichier `.pyc` inclus.

La suite complète `tests/rules` est exécutée par `apply_patch_queue.py`.
