# Changelog — 0272-r7 ProjectV2 SourceCandidate operator gate

## Added

- gate locale d'une `SourceCandidate` issue d'un handoff r6 ;
- réutilisation des décisions existantes inspect/relaunch/reject/archive/promote/merge ;
- gate record immuable et adressé par contenu ;
- refus de promouvoir ou fusionner un retrait advisory ;
- CLI opérateur `gate_github_project_v2_source_candidate_0272.py` ;
- tests de contrats, CLI et règles ;
- graphe runtime et documentation d'architecture.

## Changed

- le mode ProjectV2 direct devient explicitement le mode principal ;
- le readiness n'exige plus le pont GitHub Actions par défaut ;
- `--check-actions-bridge` contrôle volontairement le pont secondaire ;
- README et guide opérateur séparent ProjectV2 DraftIssues et repository Issues.

## Boundaries

- aucune mutation GitHub ;
- aucun réseau dans r7 ;
- aucune écriture SQL/Qdrant ;
- aucune modification Scheduler/SHM ;
- aucune dépendance non-stdlib.
