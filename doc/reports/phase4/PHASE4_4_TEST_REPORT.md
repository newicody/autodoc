# Phase 4.4 — Test report

## Scope

Phase 4.4 valide l'hygiène de découverte des sources E5 locales avant lecture, chunking et construction du corpus.

La phase reste hors Scheduler, hors Qdrant et conserve le format corpus existant.

## Commandes à exécuter

```bash
PYTHONPATH=src pytest -q tests/inference
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

Validation DOT source uniquement :

```bash
dot -Tsvg doc/docs/architecture/inference/51_e5_sources.dot >/tmp/51_e5_sources.svg
dot -Tsvg doc/docs/architecture/inference/58_e5_source_hygiene.dot >/tmp/58_e5_source_hygiene.svg
rm -f /tmp/51_e5_sources.svg /tmp/58_e5_source_hygiene.svg
```

## Résultats attendus

```text
tests/inference: passed
tests/rules: passed
full suite: passed, existing skips preserved
DOT 51: render OK
DOT 58: render OK
```

## Vérifications fonctionnelles

- Les répertoires `.git`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.tox`, `.venv`, `venv`, `build` et `dist` sont ignorés par défaut.
- Les suffixes `.pyc`, `.pyo` et `.svg` sont ignorés par défaut.
- Les exclusions personnalisées restent possibles au niveau `e5_sources.py`.
- `load_e5_corpus_documents_from_sources()` applique la même hygiène avant conversion vers `E5CorpusDocument`.
- Le format corpus reste inchangé.

## Hors périmètre

- Aucun Scheduler.
- Aucun Qdrant.
- Aucun changement de format corpus.
- Aucun SVG versionné.
- Aucun script de patch.
