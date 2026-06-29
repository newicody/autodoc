# Phase 3.13 — Sources TXT/Markdown vers corpus E5

## Objectif

Indexer un vrai dossier de notes sans écrire chaque passage à la main.

La chaîne devient :

```text
.md / .markdown / .txt
  -> E5SourceDocument
  -> E5TextChunk
  -> E5CorpusDocument
  -> E5CorpusBuilder
  -> E5CorpusIndex JSON
```

## Découpage

Le découpage est volontairement simple :

```text
paragraphes séparés par lignes vides
chunks <= --chunk-chars
option --overlap-paragraphs
métadonnées source et lignes conservées
```

Ce n’est pas encore un parser Markdown intelligent. C’est une étape de production minimale, robuste et déterministe.

## Métadonnées enregistrées

Chaque chunk converti en `E5CorpusDocument` transporte :

```text
source_path
chunk_index
start_line
end_line
source_id
source_extension
```

Ces métadonnées seront importantes plus tard pour remonter du résultat vectoriel vers le fichier source réel.

## CLI

Construire depuis un fichier :

```bash
./tools/build_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --source-file ./notes.md \
  --output /tmp/e5_corpus.json \
  --overwrite
```

Construire depuis un dossier :

```bash
./tools/build_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --source-dir ./data \
  --chunk-chars 1200 \
  --output /tmp/e5_corpus.json \
  --overwrite
```

## Limites

- Pas encore de cache incrémental.
- Pas encore de hash de fichier pour éviter le recalcul.
- Pas encore de Qdrant.
- Pas encore de stratégie de chunking par titres Markdown.

Ces limites sont volontaires : on valide d’abord le chemin local complet.
