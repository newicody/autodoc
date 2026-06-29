# Phase 3.10 — Contrat `query:` / `passage:` E5

La Phase 3.10 ajoute une couche explicite autour des rôles E5 avant l'indexation vectorielle.

## Règle E5

- `query:` représente le texte qui cherche.
- `passage:` représente le texte qui peut être retrouvé.

Pour une recherche asymétrique, la requête utilisateur doit donc être encodée en `query:` et les documents/corpus en `passage:`. Cette phase empêche d'envoyer du texte brut ambigu au pipeline E5.

## Flux

```text
query brute
  -> E5Text.query(...)
  -> "query: ..."
  -> pipeline E5
  -> vecteur query

passages bruts
  -> E5Text.passage(...)
  -> "passage: ..."
  -> pipeline E5
  -> vecteurs passages
  -> dot_product / cosine similarity
  -> ranking local
```

## Nouveaux objets

```text
E5Text
E5LocalRanker
E5RankedResults
E5RankedPassage
E5Similarity
dot_product
```

## Pourquoi avant Qdrant ?

Avant de brancher un index vectoriel externe, il faut vérifier que le modèle classe correctement quelques passages en mémoire. Le ranker local est volontairement simple : il encode une query et plusieurs passages, puis trie par produit scalaire. Comme les vecteurs E5 sont normalisés par le pipeline, ce produit scalaire correspond à une cosine similarity.

## CLI

`tools/embed_e5.py` accepte maintenant `--role`.

```bash
./tools/embed_e5.py --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --role query \
  "je me suis fait baiser"
```

équivaut à envoyer :

```text
query: je me suis fait baiser
```

Pour encoder un document :

```bash
./tools/embed_e5.py --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --role passage \
  "j'ai été arnaqué par un vendeur"
```

équivaut à envoyer :

```text
passage: j'ai été arnaqué par un vendeur
```

## Limites volontaires

- pas encore de Qdrant ;
- pas encore de batch optimisé ;
- pas encore de persistance de vecteurs ;
- pas encore de composant kernel ;
- pas encore de stratégie hybride dense/sparse.
