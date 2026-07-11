# Changelog — 0272-r8 ProjectV2 durable consumer

## Added

- validation stricte d'un gate record r7 approuvé ;
- construction d'un `SqlContextRecord` déterministe `github_artifact` ;
- consommation SQL insert-if-absent avec replay idempotent ;
- readback SQL obligatoire ;
- CLI `consume_github_project_v2_source_candidate_gate_0272.py` ;
- tests de contrat, outil et règles ;
- documentation de la suite vectorielle et laboratoire.

## Boundaries

- aucune exécution OpenVINO/E5 ;
- aucune écriture Qdrant ;
- aucune mutation GitHub ;
- aucun changement Scheduler/SHM ;
- aucune dépendance non-stdlib ;
- aucun nouveau manager/orchestrateur/store.
