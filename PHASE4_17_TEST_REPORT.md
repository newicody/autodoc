# Phase 4.17 — Test report — E5 prompt file CLI

## Objectif

Valider que la sous-commande `search` peut produire des artefacts de contexte et de prompt sans appeler de LLM.

## Commandes recommandées

```bash
PYTHONPATH=src pytest -q tests/inference/test_e5_search_prompt_file.py
PYTHONPATH=src pytest -q tests/inference/test_e5_search_context_file.py
PYTHONPATH=src pytest -q tests/inference
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Vérifications effectuées avant archive

```text
py_compile: OK sur les fichiers modifiés
DOT 70: OK
DOT 71: OK
aucun SVG inclus
aucun __pycache__ inclus
aucun script patch
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 4.17 applique les règles Phase 4.12-r2 et la règle stdlib introduite en 4.14 ; aucune nouvelle guideline n'est nécessaire.
```
