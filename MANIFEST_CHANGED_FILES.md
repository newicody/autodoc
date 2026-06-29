# MANIFEST — Phase 2.1 changed files

## Objectif

Ajouter `ReplayScenarioRunner` et `ReplayReport` pour comparer plusieurs résultats de `ReplaySandbox` dans un rapport déterministe, sans réinjecter de replay dans le Scheduler vivant.

## Fichiers ajoutés

```text
src/observability/replay_scenario.py
tests/observability/test_replay_scenario.py
doc/CHANGELOG_PHASE2_1.md
PHASE2_1_TEST_REPORT.md
```

## Fichiers modifiés

```text
src/contracts/replay.py
src/observability/__init__.py
doc/ARCHITECTURE_LAYERS.md
doc/docs/architecture/00_global.dot
doc/docs/architecture/observability/70_observability.dot
doc/docs/architecture/tests/80_tests.dot
```

## Fichiers volontairement non fournis

```text
*.svg
scripts de patch
```

Les SVG restent générés localement via le `makefile` du dossier `doc`.

## Validation

```text
39 passed
main.py exit code: 0
DOT_OK
```
