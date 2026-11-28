# Phase 3.12 — Corpus local E5 persistant

## Objectif

La phase 3.12 ajoute une étape intermédiaire avant Qdrant : un corpus local JSON contenant des passages déjà vectorisés.

Le but est d'éviter ce comportement coûteux :

```text
query -> recalculer tous les passages -> scores
```

et de passer à :

```text
build corpus : passages -> embeddings -> corpus.json
search      : query -> embedding -> scores contre corpus.json
```

## Position dans l'architecture

Le corpus local reste hors Scheduler. Il ne publie aucun événement et ne commande aucun composant.

```text
OpenVINOEmbeddingPipeline
  -> E5CorpusBuilder
  -> E5CorpusIndex
  -> E5CorpusJsonStore
  -> E5CorpusSearcher
```

## Classes ajoutées

```text
E5CorpusDocument
E5CorpusEmbedding
E5CorpusIndex
E5CorpusBuilder
E5CorpusSearcher
E5CorpusSearchHit
E5CorpusSearchResults
E5CorpusJsonStore
```

## Persistance

Le format est JSON stable avec le schéma :

```text
missipy.e5.corpus.v1
```

Il contient :

```text
model
backend
tokenizer
dimension
metadata
embeddings[]
```

Chaque embedding contient :

```text
id
text
prefixed_text
vector
dimension
normalized
l2_norm
metadata
```

## Commandes de développement

Construire un corpus :

```bash
./tools/build_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --output /tmp/e5_corpus.json \
  --passage "j'ai été arnaqué par un vendeur" \
  --passage "problème moteur diesel" \
  --passage "documentation OpenVINO"
```

Rechercher dans ce corpus :

```bash
./tools/search_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --index /tmp/e5_corpus.json \
  --limit 3 \
  "je me suis fait baiser"
```

## Limites volontaires

Cette phase ne remplace pas Qdrant. Elle sert de banc de test local.

Elle ne gère pas encore :

```text
suppression incrémentale
mise à jour partielle
métadonnées riches
filtrage avancé
pagination
index ANN
```

Ces points appartiennent à la future couche vector store.
