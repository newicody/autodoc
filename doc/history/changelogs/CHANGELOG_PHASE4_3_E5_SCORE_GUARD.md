# Changelog Phase 4.3 — E5 score guard

## Objectif

La Phase 4.3 ajoute un garde-fou local à la recherche E5 : un seuil minimal optionnel de score.

Le but est d'éviter qu'un corpus trop petit ou hors sujet retourne toujours un "meilleur" résultat présenté comme exploitable.

## Ajouté

- `E5CorpusSearcher.search(..., min_score=...)`.
- Filtrage inclusif des résultats : `score >= min_score`.
- Validation moteur : `min_score` doit être dans `[-1.0, 1.0]` lorsqu'il est fourni.
- Option CLI `search_e5_corpus.py --min-score FLOAT`.
- Validation CLI de `--min-score` avant lecture du corpus et construction du modèle.
- Tests moteur sur :
  - filtrage des hits sous le seuil ;
  - conservation d'un hit exactement égal au seuil ;
  - retour vide quand tous les hits sont filtrés ;
  - rejet d'un seuil invalide.
- Tests CLI sur :
  - parsing de `--min-score` ;
  - filtrage en sortie texte ;
  - filtrage en sortie JSON ;
  - rejet d'un seuil invalide.
- Graphe DOT `doc/docs/architecture/inference/57_e5_score_guard.dot`.
- Mise à jour du graphe DOT `doc/docs/architecture/inference/52_e5_search_report.dot` pour relier le rapport au garde-fou.

## Comportement

Sans `min_score`, le comportement historique est conservé : les hits sont triés par score décroissant puis limités par `limit`.

Avec `min_score`, le moteur :

```text
encode query
-> calcule tous les scores
-> trie par score décroissant
-> filtre score >= min_score
-> applique limit
-> renvoie les hits restants
```

Le filtrage se fait avant le rendu texte ou JSON.

## Non modifié

- Pas de Scheduler.
- Pas de Qdrant.
- Pas de format corpus.
- Pas de runtime OpenVINO supplémentaire.
- DOT source mis à jour uniquement quand notable.
- Pas de SVG versionné.
- Pas de script de patch.

## Raison

La recherche locale Phase 4.2 était techniquement exploitable, mais un top-k pur peut toujours retourner quelque chose, même sur un corpus jouet ou hors sujet.

Le seuil minimal rend ce comportement explicite : une recherche peut maintenant retourner zéro hit utile au lieu de promouvoir un résultat faible.


## Graphe architecture

La Phase 4.3 est notable pour le sous-système de recherche locale : elle ne change pas le noyau, mais elle modifie la sémantique des résultats visibles.

Le graphe dédié documente :

```text
query + corpus
-> score all hits
-> sort
-> filter score >= min_score
-> limit
-> report text/json
```

Les graphes ne versionnent que les sources `.dot`. Les SVG restent des artefacts générés.
