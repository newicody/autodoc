# Phase 4.18 — Test report — E5 dry-run artifact directory

## Objectif

Valider que la sous-commande `search` peut produire un jeu complet d'artefacts de prototype avec une seule option `--artifact-dir`, sans backend de génération.

## Commandes recommandées

```bash
PYTHONPATH=src pytest -q tests/inference/test_e5_search_artifact_dir.py
PYTHONPATH=src pytest -q tests/inference/test_e5_search_prompt_file.py
PYTHONPATH=src pytest -q tests/inference/test_e5_search_context_file.py
PYTHONPATH=src pytest -q tests/inference/test_e5_search_report_file.py::test_search_report_file_failure_returns_error
PYTHONPATH=src pytest -q tests/inference
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Vérifications effectuées avant archive

```text
py_compile: OK sur les fichiers modifiés
DOT 71: OK
DOT 72: OK
archive: .tar.gz
aucun SVG généré inclus
aucun __pycache__ inclus
aucun script patch inclus
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 4.18 applique les règles Phase 4.12-r2 et la règle stdlib introduite en 4.14 ; aucune nouvelle guideline n'est nécessaire.
```
