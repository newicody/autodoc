# Changelog Phase 1 — Scheduler bootable

## Code

- `main.py` corrigé.
- `Event` rendu fiable et extensible.
- `Request` ajouté.
- `ComponentProxy` refactorisé.
- `Scheduler` reçoit maintenant le `Registry`.
- `ContextEngine` reçoit explicitement `Registry` et `EventBus`.
- `Dispatcher` résout les futures de réponse.
- `LifecycleManager` gère `TICK`, `ERROR`, `CONTEXT_REQUEST`, `CONTEXT_REPLY`.
- `DummyExpert` converti en async generator correct.
- `contracts/inference.py` ajouté.

## Documentation

- `ARCHITECTURE_LAYERS.md` ajouté.
- `00_global.dot` mis à jour.
- `scheduler/10_scheduler.dot` mis à jour.
- `context/20_context.dot` mis à jour.
- `services/30_services.dot` mis à jour.
- vues placeholders cohérentes ajoutées pour experts, validation, learning, observability.

## Limite volontaire

OpenVINO, Qdrant, SQLite et MCTS ne sont pas encore intégrés au runtime.
Ils sont documentés comme layers futurs et doivent passer par Events/adapters.
