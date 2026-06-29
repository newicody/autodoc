# CHANGELOG — Phase 2.0

## Objectif

Ajouter un `ReplaySandbox` minimal pour commencer le replay contrôlé sans réinjecter d'événements dans le Scheduler de production.

## Décision architecturale

Le replay effectif ne passe pas encore par le kernel courant.

Le flux Phase 2.0 devient :

```text
EventLogSnapshot
  -> ReplayReader
  -> ReplayPlan
  -> ReplaySandbox
  -> ReplaySandboxResult
```

Le `ReplaySandbox` :

- ne connaît pas le Scheduler ;
- ne publie aucun `Event` ;
- ne reconstruit pas `Request.reply` ;
- ne désérialise pas automatiquement `payload_repr` ;
- refuse `SHUTDOWN` par défaut ;
- peut restreindre explicitement les types rejouables ;
- peut appeler des handlers de simulation synchrones.

## Fichiers ajoutés

```text
src/observability/replay_sandbox.py
tests/observability/test_replay_sandbox.py
doc/CHANGELOG_PHASE2_0.md
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
```

Résultat attendu :

```text
35 passed
main.py exit code: 0
```
