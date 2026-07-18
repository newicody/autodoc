# Rapport de test — 0287 r16-r13

## Unité

`projeter-separement-les-deux-analyses-dans-qdrant`

## Portée

- lecture du reçu SQL r16-r12;
- construction de deux plans de probe distincts;
- validation de l’attestation E5-384 et de la collection;
- inspection read-only des deux objets;
- exécution séquentielle des deux probes live;
- persistance SQL des deux métadonnées de projection;
- relecture et réhydratation SQL des deux points;
- aucune synthèse ni mutation GitHub.

## Vérifications du bundle

- compilation Python : réussie;
- contrôle statique des frontières : réussi;
- `git apply --check` sur une base vide : réussi;
- `git diff --check` : réussi.

La suite complète `tests/rules` est exécutée par `apply_patch_queue.py`.
