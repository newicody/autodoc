# Rapport de test — 0287 r16-r19

## Unité

`cabler-et-valider-cycle-complet-recherche-github`

## Portée

- composition explicite r16-r7 → r16-r18;
- arrêt au premier échec;
- conservation du Scheduler comme orchestrateur unique;
- frontière de confirmation entre préparation et mutation distante;
- publication exécutée une seule fois;
- clôture SQL uniquement après readback distant valide;
- aucune nouvelle infrastructure ou couche de transport.

## Vérifications du bundle

- analyse syntaxique AST : réussie;
- contrôle statique des frontières : réussi;
- ordre des treize étapes verrouillé par test;
- `git apply --check` sur une base vide enrichie des fichiers modifiés : réussi;
- `git diff --check` : réussi;
- aucun `__pycache__` ou fichier `.pyc` inclus.

La suite complète `tests/rules` est exécutée par `apply_patch_queue.py`.
