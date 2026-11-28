# CHANGELOG Phase 2.5 — BackendRegistry minimal

## Ajouté

- `src/inference/registry.py`
  - `BackendRegistry`
  - `BackendRegistrySnapshot`
- Tests dédiés du registre de backends.

## Modifié

- `InferenceAdapter` dépend maintenant de `BackendRegistry` au lieu de stocker
  directement les backends.
- `Launcher` construit explicitement :

```text
DummyInferenceBackend
  -> BackendRegistry
  -> InferenceAdapter
  -> InferenceRequestHandler
```

- La roadmap inference DOT montre désormais `BackendRegistry` comme membrane de
  sélection.

## Non modifié

- Scheduler
- Dispatcher
- ComponentProxy
- EventBus
- OpenVINO
- Qdrant
- SQLite

## Motivation

Préparer l'intégration future d'OpenVINO sans coupler le kernel à un backend IA
concret. Le choix du backend devient explicite, testable et observable.
