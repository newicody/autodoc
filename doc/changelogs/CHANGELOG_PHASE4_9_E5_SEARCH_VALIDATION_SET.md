# Changelog Phase 4.9 — E5 search validation set

## Objectif

La Phase 4.9 remplace la validation recherche ponctuelle du rebuild sûr par un jeu de requêtes de validation.

Le rebuild peut maintenant vérifier plusieurs intentions de recherche avant promotion du corpus candidat.

Flux :

```text
source-dir / passages
-> build staging
-> diagnostic gate optionnel
-> search validation set
-> promotion finale seulement si toutes les requêtes passent
```

## Ajouté

- `src/inference/e5_search_validation.py`
  - `E5SearchValidationQueryResult`
  - `validate_e5_search_queries()`
- `rebuild_e5_corpus.py`
  - `--validation-query` répétable ;
  - `--validation-queries-file` répétable ;
  - `--validation-min-score` ;
  - échec contrôlé `exit 2` si une requête ne produit aucun hit.
- Rapports rebuild texte et JSON enrichis :
  - `validation_query_count` ;
  - `validation_min_score` ;
  - `validation_passed` ;
  - détail JSON de chaque requête.
- Tests dédiés du validateur recherche.
- Tests d'intégration CLI rebuild avec plusieurs requêtes et fichier de requêtes.
- Graphe DOT `63_e5_search_validation_set.dot`.

## Modifié

- `src/inference/e5_rebuild_cli.py`
  - la validation recherche se fait maintenant après le diagnostic gate et avant promotion ;
  - le staging est nettoyé sur échec, sauf `--keep-staging`.
- `doc/docs/architecture/inference/62_e5_rebuild_diagnostic_gate.dot`
  - ajout du lien de navigation vers la Phase 4.9.

## Non modifié

- Pas de Scheduler.
- Pas de Qdrant.
- Pas de changement du format `missipy.e5.corpus.v1`.
- Pas de changement du moteur d'embedding.
- Pas de SVG versionné.
- Pas de script de patch.

## Raison

Une unique requête de validation peut masquer un corpus partiellement mauvais.

Le jeu de validation permet de vérifier plusieurs intentions importantes avant de remplacer l'index final.
