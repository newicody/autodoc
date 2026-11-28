# Changelog — 0272-r6 GitHub ProjectV2 change handoff

## Added

- conversion locale des change sets r4 en lots de handoffs immuables ;
- réutilisation de `SourceCandidate` pour chaque changement ProjectV2 ;
- politique bornée `max_handoffs` ;
- prise en charge explicite des ajouts, modifications et retraits advisory ;
- CLI opérateur `build_github_project_v2_change_handoffs_0272.py` ;
- documentation complète de configuration manuelle ProjectV2/GitHub Actions ;
- graphe runtime et extension du graphe canonique ;
- tests de contrats, CLI et règles.

## Changed

- les summaries r4 des items ajoutés/retirés conservent maintenant le corps du
  contenu afin de ne pas perdre la matière d'une `DRAFT_ISSUE` avant handoff ;
- le README racine expose la procédure GitHub Actions et la troisième commande
  du flux entrant ;
- le `.ini` documente la politique locale de handoff.

## Boundaries

- aucune mutation GitHub ;
- aucun appel réseau dans r6 ;
- aucune écriture SQL/Qdrant ;
- aucune modification Scheduler/SHM ;
- aucune dépendance non-stdlib.
