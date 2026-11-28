# Phase 3.14 — Rapport de résultats E5 avec contexte source

## Objectif

La recherche dans `corpus.json` ne doit pas seulement renvoyer un score et un texte brut. Quand le corpus vient de fichiers `.md`, `.markdown` ou `.txt`, le résultat doit indiquer d'où vient le chunk.

La chaîne devient :

```text
query
  -> E5CorpusSearcher
  -> E5CorpusSearchResults
  -> E5SearchReport
  -> score + source_path + lignes + extrait
```

## Nouveau rapport

`E5SearchReport` transforme les hits bruts en résultats exploitables pour une CLI ou un futur outil web :

```text
rank
score
id
source_path
start_line / end_line
chunk_index
excerpt
metadata
```

Le texte complet du chunk reste disponible, mais il n'est pas affiché par défaut pour éviter des sorties trop longues.

## CLI

Recherche avec extrait court :

```bash
./tools/search_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --index /tmp/e5_corpus.json \
  --excerpt-chars 180 \
  "je cherche une arnaque vendeur"
```

Inclure le texte complet :

```bash
./tools/search_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --index /tmp/e5_corpus.json \
  --full-text \
  "je cherche une arnaque vendeur"
```

Sortie JSON :

```bash
./tools/search_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --index /tmp/e5_corpus.json \
  --format json \
  "je cherche une arnaque vendeur"
```

## Limites

- Pas encore de lecture du fichier source à la volée autour des lignes trouvées.
- Pas encore de surlignage des termes.
- Pas encore de fusion de chunks voisins.
- Pas encore de Qdrant.

Cette phase prépare le rendu exploitable des résultats avant d'introduire un vrai moteur vectoriel externe.
