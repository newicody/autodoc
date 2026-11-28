# CHANGELOG — Phase 2.1

## Objectif

Ajouter `ReplayScenarioRunner` et `ReplayReport` pour comparer plusieurs résultats de replay sandbox dans un rapport déterministe.

## Décision architecturale

Le replay reste hors du Scheduler vivant.

Le flux Phase 2.1 devient :

```text
EventLogSnapshot
  -> ReplayReader
  -> ReplayPlan
  -> ReplaySandbox
  -> ReplaySandboxResult
  -> ReplayScenarioRunner
  -> ReplayReport
```

Le `ReplayScenarioRunner` :

- ne connaît pas le Scheduler ;
- ne publie aucun `Event` ;
- utilise `ReplaySandbox` comme moteur isolé ;
- partage éventuellement des handlers de simulation ;
- agrège les résultats dans un `ReplayReport` immuable.

Le `ReplayReport` :

- expose les totaux acceptés/refusés/manipulés ;
- indique si tous les scénarios sont valides ;
- produit des lignes textuelles déterministes ;
- ne contient pas d'horodatage runtime.

## Fichiers ajoutés

```text
src/observability/replay_scenario.py
tests/observability/test_replay_scenario.py
CHANGELOG_PHASE2_1.md
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

## Validation

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

Résultat attendu :

```text
39 passed
main.py exit code: 0
DOT_OK
```
