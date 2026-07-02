# Changelog — Phase 3.10 — E5 query/passage

## Added

- `src/inference/e5_text.py`
  - `E5Text`
  - `ensure_e5_text()`
  - `detect_e5_role()`
  - constantes `query` / `passage`.
- `src/inference/e5_ranker.py`
  - `E5LocalRanker`
  - `E5RankedResults`
  - `E5RankedPassage`
  - `E5Similarity`
  - `dot_product()`.
- Tests unitaires pour le contrat query/passage et le ranker local.
- Documentation `doc/MODEL_E5_QUERY_PASSAGE_PHASE3_10.md`.
- Graphe DOT `49_e5_query_passage.dot`.

## Changed

- `tools/embed_e5.py` via `inference.e5_cli` accepte maintenant `--role auto|query|passage`.
- Le texte brut CLI est préfixé en `query:` par défaut.
- Le texte déjà préfixé conserve son rôle.
- `src/inference/__init__.py` exporte les nouveaux contrats E5.
- Documentation README / architecture mise à jour.

## Not changed

- Aucun changement Scheduler.
- Aucun changement Dispatcher.
- Aucun changement ComponentProxy.
- Aucun Qdrant.
- Aucun batch vectoriel optimisé.
- Aucun SVG généré ni inclus.
