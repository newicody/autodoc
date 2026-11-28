# Changelog Phase 1.1

## Kernel

- Ajout de `contracts.lifecycle.ComponentState`.
- `ComponentProxy` possède maintenant un état observable.
- `ComponentProxy.context()` retourne l'état du proxy + le contexte réel du composant.
- `Dispatcher` retourne un résultat explicite pour les événements sans handler.
- `Scheduler.shutdown()` est traité après les événements déjà en file par défaut, pour éviter de perdre `STOP`.
- `LifecycleManager` devient une instance testable qui maintient `states` et `errors`.

## Contracts

- `Event.id` reste basé sur `uuid.uuid4().hex`.
- `Request.reply` reste séparé du payload.
- Ajout de `ComponentState`.

## Tests

Ajout d'une suite pytest :

- `tests/kernel/test_event_and_dispatcher.py`
- `tests/runtime/test_component_proxy.py`
- `tests/context/test_context_engine.py`

Résultat validé localement :

```text
7 passed
```

## Documentation

- Mise à jour de `ARCHITECTURE_LAYERS.md`.
- Mise à jour de `00_global.dot`.
- Mise à jour de `scheduler/10_scheduler.dot`.
- Mise à jour de `context/20_context.dot`.
- Ajout de `tests/80_tests.dot`.
- SVG régénérés via Graphviz.
