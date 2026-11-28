# Phase 4.11 — Test report

## Scope

Phase 4.11 ajoute un rapport JSON optionnel à la commande de recherche E5 locale.

La phase reste hors Scheduler, hors Qdrant et conserve le format corpus existant.

## Commandes à exécuter

```bash
PYTHONPATH=src pytest -q tests/inference
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

Validation DOT :

```bash
dot -Tsvg doc/docs/architecture/inference/64_e5_rebuild_report_file.dot >/tmp/64_e5_rebuild_report_file.svg
dot -Tsvg doc/docs/architecture/inference/65_e5_search_report_file.dot >/tmp/65_e5_search_report_file.svg
rm -f /tmp/64_e5_rebuild_report_file.svg /tmp/65_e5_search_report_file.svg
```

## Tests ajoutés

- Le parser accepte `--report-file`.
- La recherche JSON écrit un rapport identique à la sortie JSON.
- La recherche texte peut aussi écrire un rapport JSON.
- `--report-file /` est refusé avant lecture du corpus.
- Une erreur d'écriture du rapport retourne un code 1.

## Verdict attendu

```text
Phase 4.11 search report file: OK
Phase 4.11 corpus format unchanged: OK
Phase 4.11 Scheduler untouched: OK
Phase 4.11 Qdrant untouched: OK
```

## Hors périmètre

- Aucun Scheduler.
- Aucun Qdrant.
- Aucun changement de format corpus.
- Aucun SVG versionné.
- Aucun script de patch.
