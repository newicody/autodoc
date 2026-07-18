# Rapport de test — 0287 r16-r7

## Unité

`assembler-les-recherches-recuperees-et-verifier-leur-admissibilite`

## Portée

- ajout d’un contrat pur d’assemblage d’un `ready_run`;
- ajout d’un adaptateur local lisant le rapport du fetch canonique;
- réutilisation de l’assemblage dual 0281;
- réutilisation du paquet corrélé 0287;
- réutilisation du verrou d’admissibilité r16-r6;
- aucune commande Scheduler et aucune exécution laboratoire.

## Vérifications du bundle

- `python -m compileall`: réussi;
- tests unitaires isolés du nouveau contrat: réussis;
- `git diff --check`: réussi;
- `git apply --check` sur une base vide: réussi.

La suite complète `tests/rules` doit être exécutée par
`apply_patch_queue.py` dans le checkout utilisateur.
