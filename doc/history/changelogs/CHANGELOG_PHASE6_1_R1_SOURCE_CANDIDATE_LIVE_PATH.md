# Changelog — Phase 6.1-r1 — SourceCandidate live path

## Ajouté

- `src/context/source_candidate_intake.py`
  - `SourceCandidateIntakeCommand`
  - `SourceCandidateIntakeResult`
  - `run_source_candidate_intake()`
- `src/context/source_candidate_handlers.py`
  - `SourceCandidateIntakeHandler`
  - publication observable `SOURCE_CANDIDATE_INTAKE_RESULT`
- `tests/context/test_source_candidate_live_path.py`
  - test PolicyEngine destination `source_candidate`
  - test d'intégration Scheduler -> Handler -> store JSON réel -> EventBus
- `doc/code-rules/PHASE6_1_R1_CODE_RULE_ALIGNMENT.md`
- `doc/docs/architecture/context/44_source_candidate_intake_live_path.dot`

## Modifié

- `src/contracts/event.py`
  - ajout `SOURCE_CANDIDATE_INTAKE`
  - ajout `SOURCE_CANDIDATE_INTAKE_RESULT`
- `src/policy/engine.py`
  - ajout de la destination autorisée `source_candidate`
- `src/context/source_candidate_intake_cli.py`
  - la CLI produit toujours une commande typée ;
  - `main()` passe désormais par un Scheduler local vivant ;
  - `run_source_candidate_intake()` reste disponible pour tests/unitaires via import du module pur.
- DOT global et DOT 43 mis à jour pour pointer vers 44.

## Non modifié

- Pas de modification du Scheduler.
- Pas de serveur.
- Pas de GitHub API.
- Pas de Qdrant.
- Pas de LLM.
- Pas d'appel OpenVINO.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.
