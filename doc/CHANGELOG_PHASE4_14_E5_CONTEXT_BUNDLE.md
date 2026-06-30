# Phase 4.14 — E5 context bundle

## Objectif

Produire un bundle de contexte JSON depuis les hits `search_e5_corpus.py`, sans ajouter de nouveau script CLI et sans changer le format `missipy.e5.corpus.v1`.

## Changements

- Ajout de `src/inference/e5_context_bundle.py` :
  - `E5ContextBundleItem` ;
  - `E5ContextBundle` ;
  - projection `to_json_dict()` ;
  - projection `to_text()`.
- Ajout de l'option `search --context-file FILE`.
- Le bundle est construit depuis `E5SearchReport`, donc il réutilise les hits, sources, lignes et extraits déjà validés.
- L'écriture JSON reste centralisée via `report_io.write_json_report_atomic()`.
- La surface CLI n'est pas élargie par un nouveau script : on étend la sous-commande `search` existante.
- `doc/code_rule.md` reçoit la règle explicite sur les bibliothèques hors stdlib.

## Hors périmètre

- Pas de Qdrant.
- Pas de Scheduler.
- Pas de LLM/réponse générée.
- Pas de changement du format corpus.
- Pas de nouveau script `tools/`.
- Pas de dépendance hors bibliothèque standard.

## code_rule

```text
code_rule_review: done
code_rule_update_required: true
code_rule_reason: ajout de la règle demandée sur les bibliothèques hors stdlib ; 4.14 n'ajoute aucune dépendance externe.
```
