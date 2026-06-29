# CHANGELOG — Phase 1.9

## Ajout

- Ajout de `ReplayEvent` et `ReplayPlan` dans `contracts.replay`.
- Ajout de `observability.replay_reader.ReplayReader`.
- Ajout de tests dédiés au lecteur de replay.

## Architecture

- Le replay reste dans `observability`.
- `ReplayReader` lit un `EventLogSnapshot` produit par `EventRecorder`.
- `ReplayReader` ne connaît pas le Scheduler.
- `ReplayReader` ne publie aucun événement.
- `ReplayReader` ne reconstruit pas `Request.reply`.
- Le payload reste sous forme `payload_repr`.

## Flux Phase 1.9

```text
EventBus.publish(Event)
  -> EventRecorder
  -> EventRecord
  -> EventLogSnapshot
  -> ReplayReader
  -> ReplayPlan
```

## DOT

Fichiers DOT modifiés uniquement parce que la roadmap observability/replay évolue :

- `doc/docs/architecture/00_global.dot`
- `doc/docs/architecture/observability/70_observability.dot`
- `doc/docs/architecture/tests/80_tests.dot`

Aucun SVG généré.

## Tests

Validation effectuée :

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
```

Résultat attendu :

```text
29 passed
main.py exit code: 0
```
