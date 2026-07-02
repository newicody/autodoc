# CHANGELOG — Phase 3.14 E5 search report

## Ajouté

- `src/inference/e5_search_report.py` : rapport lisible des résultats de recherche E5.
- `E5SearchReportConfig` : configuration d'extrait et option texte complet.
- `E5SearchSourceContext` : extraction de `source_path`, `start_line`, `end_line`, `chunk_index`, `source_id`, `source_extension` depuis les métadonnées de chunk.
- `E5SearchReportHit` : hit enrichi avec score, extrait et contexte source.
- `E5SearchReport` : projection texte/JSON stable d'une recherche locale.
- `make_excerpt()` : extrait mono-ligne déterministe.
- Options CLI sur `search_e5_corpus.py` via `e5_corpus_cli` :
  - `--excerpt-chars`
  - `--full-text`
- Tests unitaires du rapport et des nouvelles options CLI.
- Roadmap DOT `inference/52_e5_search_report.dot`.

## Modifié

- `src/inference/e5_corpus_cli.py` utilise désormais `E5SearchReport` pour le rendu des résultats.
- `README.md` et `ARCHITECTURE_LAYERS.md` mentionnent la phase 3.14.
- `doc/docs/architecture/inference/40_inference.dot`, `50_e5_corpus.dot` et `tests/80_tests.dot` ajoutent la brique rapport.

## Non ajouté

- Pas de Qdrant.
- Pas de lecture de contexte fichier autour des lignes depuis le disque.
- Pas de surlignage de requête.
- Pas de fusion de chunks adjacents.
- Pas de modification Scheduler.
- Pas de SVG inclus.

## Raison

Le prototype doit afficher des résultats exploitables avant Qdrant : un score seul ne suffit pas. Le rapport rend le corpus local utilisable en indiquant le fichier, les lignes et un extrait stable.
