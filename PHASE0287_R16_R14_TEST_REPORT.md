# Rapport de test — 0287 r16-r14

## Unité

`rappeler-et-rehydrater-les-deux-analyses-sans-synthese`

## Portée

- validation de la lignée r16-r12/r16-r13;
- construction d’un filtre hybride depuis le scope de projection;
- requête bornée à deux résultats regroupés par source;
- réutilisation de l’exécution hybride asynchrone existante;
- exigence des deux références SQL exactes;
- conservation des corps uniquement en mémoire;
- aucun write, projection, Scheduler, spécialiste ou synthèse.

## Vérifications du bundle

- compilation Python : réussie;
- contrôle statique des frontières : réussi;
- `git apply --check` sur une base vide : réussi;
- `git diff --check` : réussi.

La suite complète `tests/rules` est exécutée par `apply_patch_queue.py`.
