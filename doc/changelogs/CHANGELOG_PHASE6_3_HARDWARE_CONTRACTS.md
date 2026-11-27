# Changelog — Phase 6.3 — Hardware observation contracts

## Ajouté

- `src/contracts/hardware.py`
  - contrats immuables et versionnés `HardwareSample` et `HardwareCell`
  - métriques et erreurs de collecte typées
  - séparation explicite de l'état physique et de l'inventaire Scheduler
  - états inconnus distincts de zéro, fraîcheur distincte de disponibilité
  - validation stricte des références, unités, valeurs, horodatages et cohérence des réservations
  - sérialisation et réhydratation par mapping

- `tests/contracts/test_hardware.py`
  - validation des schémas et de l'immutabilité
  - cohérence des statuts de collecte
  - validation des métriques et des réservations
  - round-trip des deux contrats
  - séparation des plans physique et Scheduler

## Non modifié

- `missipy.cell.v1` reste inchangé.
- Aucun changement au Scheduler, à l'EventBus ou au runtime 0287.
- Aucun collecteur OS, polling, service OpenRC ou démarrage automatique.
- Aucun raccord VisPy ou Copilot dans cette phase.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.
