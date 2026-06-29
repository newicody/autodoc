# Changelog Phase 4.4 — E5 source hygiene

## Objectif

La Phase 4.4 ajoute une hygiène déterministe à la découverte des sources E5 locales.

Elle protège les commandes qui indexent un dossier, notamment `--source-dir .`, contre l'ingestion de répertoires techniques, caches et artefacts générés.

## Ajouté

- `DEFAULT_E5_EXCLUDED_DIR_NAMES` dans `src/inference/e5_sources.py`.
- `DEFAULT_E5_EXCLUDED_FILE_SUFFIXES` dans `src/inference/e5_sources.py`.
- `E5SourceDiscoveryConfig` pour normaliser les extensions, répertoires exclus et suffixes exclus.
- Filtrage des chemins avant lecture UTF-8.
- Tests d'exclusion par défaut des répertoires parasites.
- Tests d'exclusion des suffixes parasites.
- Tests de configuration personnalisée de découverte.
- Tests de conversion source -> `E5CorpusDocument` avec hygiène active.

## Exclusions par défaut

Répertoires :

```text
.git
__pycache__
.pytest_cache
.mypy_cache
.ruff_cache
.tox
.venv
venv
build
dist
```

Suffixes :

```text
.pyc
.pyo
.svg
```

## Non modifié

- Pas de Scheduler.
- Pas de Qdrant.
- Pas de changement du format `missipy.e5.corpus.v1`.
- Pas de nouveau backend.
- Pas de modification OpenVINO.
- Pas de SVG versionné.
- Pas de script de patch.

## Raison

La recherche locale est maintenant exploitable et filtrable par score. La prochaine source de bruit vient de l'ingestion : un corpus construit depuis la racine du dépôt doit ignorer les chemins techniques sans demander une discipline manuelle permanente.

La logique reste centralisée dans `e5_sources.py` afin que les commandes de build et de rebuild sûr partagent la même hygiène.
