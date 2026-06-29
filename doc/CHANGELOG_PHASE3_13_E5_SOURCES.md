# CHANGELOG — Phase 3.13 E5 sources TXT/Markdown

## Ajouté

- `src/inference/e5_sources.py` : découverte, chargement et découpage déterministe de sources `.md`, `.markdown` et `.txt`.
- `E5SourceDocument` : source locale lue depuis fichier.
- `E5TextChunk` : chunk de passage avec `source_path`, `chunk_index`, `start_line`, `end_line`.
- Conversion `E5TextChunk -> E5CorpusDocument` pour réutiliser `E5CorpusBuilder`.
- Options CLI sur `build_e5_corpus.py` via `e5_corpus_cli` :
  - `--source-file`
  - `--source-dir`
  - `--source-extensions`
  - `--no-recursive`
  - `--chunk-chars`
  - `--overlap-paragraphs`
- Tests unitaires du loader source et des nouvelles options CLI.
- Roadmap DOT `inference/51_e5_sources.dot`.

## Non ajouté

- Pas de parser Markdown avancé.
- Pas de Qdrant.
- Pas de déduplication inter-fichiers.
- Pas de Scheduler modifié.
- Pas de SVG inclus.

## Raison

Cette phase transforme le corpus local en prototype réellement exploitable sur un dossier de notes, tout en conservant un format JSON simple, déterministe et vérifiable avant l’introduction d’un moteur vectoriel externe.
