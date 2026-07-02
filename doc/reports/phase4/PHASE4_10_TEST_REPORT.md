# Phase 4.10 — Test report

## Scope

Phase 4.10 ajoute un rapport JSON optionnel au rebuild sûr du corpus E5.

La phase reste locale, hors Scheduler, hors Qdrant, et conserve le format corpus existant.

## Commandes à exécuter

```bash
PYTHONPATH=src pytest -q tests/inference
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

Validation DOT :

```bash
dot -Tsvg doc/docs/architecture/inference/63_e5_search_validation_set.dot >/tmp/63_e5_search_validation_set.svg
dot -Tsvg doc/docs/architecture/inference/64_e5_rebuild_report_file.dot >/tmp/64_e5_rebuild_report_file.svg
rm -f /tmp/63_e5_search_validation_set.svg /tmp/64_e5_rebuild_report_file.svg
```

## Tests ajoutés

- `tests/inference/test_e5_rebuild_report_file.py`
  - parser rebuild accepte `--report-file` ;
  - le rapport JSON correspond à la sortie JSON CLI ;
  - le rapport est écrit en dry-run avec `promoted: false` ;
  - une erreur d'écriture du rapport retourne un code d'erreur contrôlé.

## Commande de validation manuelle

```bash
PYTHONPATH=src ./tools/rebuild_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --source-dir . \
  --validation-query "rebuild sûr staging promotion" \
  --validation-query "OpenVINO multilingual-e5-small local" \
  --validation-min-score 0.80 \
  --report-file /tmp/autodoc_e5_rebuild_report.json
```

## Verdict attendu

```text
Phase 4.10 rebuild report option: OK
Phase 4.10 report JSON stable: OK
Phase 4.10 dry-run report: OK
Phase 4.10 corpus format unchanged: OK
```

## Hors périmètre

- Aucun Scheduler.
- Aucun Qdrant.
- Aucun changement de format corpus.
- Aucun SVG.
- Aucun script de patch.
