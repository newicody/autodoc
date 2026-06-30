# Phase 4.15 — E5 context consumer contract — Test report

## Objectif

Ajouter un contrat pur de consommation du `E5ContextBundle` pour préparer le futur prototype question -> contexte -> réponse.

## Périmètre

Inclus :

- `E5ContextConsumptionPolicy` ;
- `E5ConsumedContextItem` ;
- `E5ConsumedContext` ;
- `consume_e5_context_bundle()` ;
- budget de caractères déterministe ;
- projections `to_json_dict()` et `to_text()`.

Exclus :

- Qdrant ;
- Scheduler ;
- LLM ;
- nouvelle CLI ;
- modification du format `missipy.e5.corpus.v1` ;
- dépendance externe.

## Vérifications faites pendant la génération

- `python -m py_compile` sur les fichiers Python modifiés ;
- validation DOT 68 et DOT 69 avec `dot -Tsvg` vers `/tmp` ;
- absence de `.svg` dans l'archive ;
- absence de `__pycache__` dans l'archive ;
- absence de script de patch.

## Tests recommandés

```bash
PYTHONPATH=src pytest -q tests/inference/test_e5_context_consumer.py
PYTHONPATH=src pytest -q tests/inference
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Dépendances

No new non-stdlib dependency.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: le contrat de consommation applique les règles Phase 4.12-r2 existantes ; aucune nouvelle guideline n'est nécessaire.
```
