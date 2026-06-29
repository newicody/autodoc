# Manifest — Phase 1.5 changed files

## Code

- `src/inference/adapter.py`
- `src/inference/handlers.py`
- `src/inference/__init__.py`
- `src/kernel/launcher.py`

## Tests

- `tests/inference/test_dummy_inference.py`

## Documentation

- `doc/ARCHITECTURE_LAYERS.md`
- `doc/CHANGELOG_PHASE1_5.md`

## DOT roadmap

- `doc/docs/architecture/00_global.dot`
- `doc/docs/architecture/scheduler/10_scheduler.dot`
- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/tests/80_tests.dot`

Aucun SVG n'est inclus.
Aucun script de patch n'est inclus.

## Raison architecturale

La Phase 1.5 ajoute `InferenceAdapter` comme membrane stable :

```text
InferenceRequestHandler
  -> InferenceAdapter
  -> DummyInferenceBackend actuel
  -> OpenVINOBackend futur
```

Le Scheduler, le Dispatcher et le ComponentProxy ne changent pas de rôle. OpenVINO pourra être ajouté derrière l'adapter sans coupler le noyau à un backend IA concret.
