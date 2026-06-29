# Manifest — Phase 1.4 changed files

## Code

- `src/contracts/inference.py`
- `src/inference/__init__.py`
- `src/inference/backend.py`
- `src/inference/handlers.py`
- `src/kernel/launcher.py`
- `src/kernel/scheduler.py`
- `src/kernel/context_engine.py`

## Tests

- `tests/inference/test_dummy_inference.py`

## Documentation

- `doc/ARCHITECTURE_LAYERS.md`
- `doc/CHANGELOG_PHASE1_4.md`

## DOT roadmap

- `doc/docs/architecture/00_global.dot`
- `doc/docs/architecture/scheduler/10_scheduler.dot`
- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/tests/80_tests.dot`

Aucun SVG n'est inclus.
Aucun script de patch n'est inclus.

## Raison architecturale

La Phase 1.4 introduit un backend d'inférence fictif pour valider le chemin :

```text
Event(INFERENCE_REQUEST)
  -> Scheduler
  -> PriorityQueue
  -> Dispatcher
  -> InferenceRequestHandler
  -> DummyInferenceBackend
  -> InferenceResult
  -> Request.reply
```

OpenVINO reste futur et ne doit pas être branché directement au Scheduler.
