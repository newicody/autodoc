# Phase 0287-r7-r6-r1 — correction du budget documentaire d’installation

## Cause

Le patch `0287-r7-r6` a correctement ajouté les chemins de publication Copilot
v2, mais a copié le mode opératoire détaillé dans `INSTALLATION.md`. Le guide
est passé de 375 à 441 lignes, au-delà de la limite cumulative de 380 lignes
verrouillée par les règles exécutables.

## Correction

- le guide cumulatif revient à 378 lignes ;
- le marqueur `0287-r7-r6` reste visible dans le guide ;
- les commandes détaillées sont déplacées dans `COPILOT_ADVISORY_V2.md` ;
- aucun code, contrat, workflow, champ ProjectV2 ou verrou de mutation ne change.

## Vérifications attendues

- `len(INSTALLATION.md.splitlines()) < 380` ;
- les marqueurs historiques et de sécurité restent présents ;
- le runbook contient les commandes preview, execute, digest et readback ;
- la suite `tests/rules` puis la suite globale doivent être relancées.
