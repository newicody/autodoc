# Phase 4.9 — Test report

## Scope

Phase 4.9 ajoute un jeu de validation recherche E5 avant promotion du corpus candidat.

La phase reste locale, hors Scheduler, hors Qdrant, et conserve le format corpus existant.

## Commandes à exécuter

```bash
PYTHONPATH=src pytest -q tests/inference
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

Validation DOT :

```bash
dot -Tsvg doc/docs/architecture/inference/62_e5_rebuild_diagnostic_gate.dot >/tmp/62_e5_rebuild_diagnostic_gate.svg
dot -Tsvg doc/docs/architecture/inference/63_e5_search_validation_set.dot >/tmp/63_e5_search_validation_set.svg
rm -f /tmp/62_e5_rebuild_diagnostic_gate.svg /tmp/63_e5_search_validation_set.svg
```

## Tests ajoutés

- `tests/inference/test_e5_search_validation.py`
  - validation de plusieurs requêtes ;
  - application de `min_score` ;
  - résultat JSON stable ;
  - rejet des options invalides.
- `tests/inference/test_e5_rebuild_search_validation_set.py`
  - parser rebuild accepte `--validation-query` répétable ;
  - parser rebuild accepte `--validation-queries-file` ;
  - parser rebuild accepte `--validation-min-score` ;
  - promotion si toutes les requêtes passent ;
  - blocage de promotion si une requête échoue ;
  - `--keep-staging` conserve le candidat échoué ;
  - rejet de `--validation-min-score` invalide.

## Commandes de validation manuelle

```bash
PYTHONPATH=src ./tools/rebuild_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --source-dir . \
  --validation-query "rebuild sûr staging promotion" \
  --validation-query "Scheduler telemetry code_rule" \
  --validation-query "OpenVINO multilingual-e5-small local" \
  --validation-min-score 0.80
```

Avec fichier :

```bash
PYTHONPATH=src ./tools/rebuild_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --source-dir . \
  --validation-queries-file doc/e5_validation_queries.txt \
  --validation-min-score 0.80
```

## Verdict attendu

```text
Phase 4.9 search validation module: OK
Phase 4.9 rebuild validation set CLI: OK
Phase 4.9 rebuild promotion guard: OK
Phase 4.9 corpus format unchanged: OK
```

## Hors périmètre

- Aucun Scheduler.
- Aucun Qdrant.
- Aucun changement de format corpus.
- Aucun SVG.
- Aucun script de patch.
