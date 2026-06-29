# CHANGELOG — Phase 1.7

## Ajouté

- `contracts.telemetry.TelemetrySnapshot` immuable.
- `observability.telemetry.KernelTelemetry`.
- Compteurs kernel : enqueue, dequeue, dispatch, erreurs, refus policy, ticks contexte.
- Mesures : taille courante/maximale de queue, latence de queue, durée de dispatch.
- Tests observability dédiés.

## Modifié

- `Scheduler` accepte maintenant une instance optionnelle de `KernelTelemetry`.
- `Scheduler.emit()` mesure les événements acceptés ou refusés.
- `Scheduler.run()` mesure dequeue, dispatch success/error et shutdown.
- `Scheduler._clock()` compte les ticks de contexte.
- `PriorityQueue` expose `qsize()`.
- `Launcher` crée et injecte `KernelTelemetry`.
- La documentation des couches est mise à jour pour Phase 1.7.
- Les DOT `global`, `scheduler`, `observability` et `tests` sont mis à jour avec des commentaires invisibles `ROADMAP_NOTE[phase1_7]`.

## Inchangé

- Aucun SVG généré.
- Aucun script de patch ajouté.
- Aucun backend OpenVINO ajouté.
- Aucun changement de Qdrant/SQLite/MCTS.
- `EventBus` reste observation-only.
- Le Scheduler ne contient toujours pas de logique métier.

## Validation

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
```

Résultat attendu :

```text
22 passed
main.py exit code: 0
```
