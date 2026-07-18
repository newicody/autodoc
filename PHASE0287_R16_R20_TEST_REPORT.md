# Rapport de test — 0287 r16-r20

## Unité

`executer-cycle-complet-recherche-github`

## Portée

- chargement d’un ready_run réel depuis le rapport de fetch;
- réutilisation du chargeur sécurisé des trois artefacts;
- import d’une fabrique de runtime existante;
- acquisition et fermeture d’une lease process-locale;
- phase `prepare` arrêtée au digest;
- phase `complete` sans recalcul local;
- réutilisation de l’adaptateur GitHub CLI existant;
- publication puis clôture SQL;
- blocage du mauvais digest avant acquisition du runtime.

## Vérifications du bundle

- analyse syntaxique AST : réussie;
- contrôle statique des frontières : réussi;
- tests isolés des deux modes : définis;
- `git apply --check` sur une base contenant le README cumulatif : réussi;
- `git diff --check` : réussi;
- aucun `__pycache__` ou fichier `.pyc` inclus.

La suite complète `tests/rules` est exécutée par `apply_patch_queue.py`.
