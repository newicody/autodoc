
# Changelog — Phase 6.2 — SourceCandidate review queue

## Ajouté

- `src/context/source_candidate_review.py`
  - `SourceCandidateReviewCommand`
  - `SourceCandidateReviewPolicy`
  - `SourceCandidateReviewItem`
  - `SourceCandidateReviewResult`
  - `run_source_candidate_review()`
- `src/context/source_candidate_review_cli.py`
  - adaptateur opérateur fin autour du chemin Scheduler vivant
- `tests/context/test_source_candidate_review.py`
  - tests du use-case pur, filtres, limite, preview et JSON stable
- `tests/context/test_source_candidate_review_live_path.py`
  - test Scheduler -> Dispatcher -> Handler -> store JSON réel -> EventBus
- `tests/context/test_source_candidate_review_cli.py`
  - test de l'adaptateur CLI de review
- `tests/rules/test_source_candidate_review_live_path_rule.py`
  - garde anti-régression pour éviter que la review redevienne un chemin CLI direct

## Modifié

- `src/contracts/event.py`
  - ajout `SOURCE_CANDIDATE_REVIEW`
  - ajout `SOURCE_CANDIDATE_REVIEW_RESULT`
- `src/context/source_candidate_handlers.py`
  - ajout `SourceCandidateReviewHandler`
  - ajout `source_candidate_review_result_payload()`

## Non modifié

- Pas de modification du Scheduler.
- Pas de serveur.
- Pas de GitHub API.
- Pas de Qdrant.
- Pas de LLM.
- Pas d'appel OpenVINO.
- Pas d'écriture de rapport review fichier dans cette tranche : le résultat JSON est stable, mais l'écriture atomique commune sera ajoutée plus tard si nécessaire.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.
