# Manifest — Phase 2.9 — RealOpenVINORuntime isolé

## Runtime / inference

- `src/inference/openvino_runtime.py`
  - ajoute `RealOpenVINORuntime`, import OpenVINO isolé, cache de modèles compilés, état observable et erreurs stables.
- `src/inference/openvino_backend.py`
  - expose dans `state().metadata` si le runtime injecté est un vrai runtime OpenVINO.
- `src/inference/__init__.py`
  - exporte les nouveaux symboles du runtime.

## Tests

- `tests/inference/test_openvino_runtime.py`
  - vérifie le runtime avec faux module OpenVINO injecté ;
  - vérifie le cache de `CompiledModel` ;
  - vérifie l'erreur si aucune entrée brute n'est fournie ;
  - vérifie le cas OpenVINO non installé.

## Documentation

- `README.md`
- `doc/ARCHITECTURE_LAYERS.md`
- `doc/OPENVINO_MODEL_STRATEGY.md`
- `doc/CHANGELOG_PHASE2_9_OPENVINO_RUNTIME.md`

## Roadmap DOT

- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/inference/41_openvino_backend.dot`
- `doc/docs/architecture/inference/42_openvino_runtime.dot`
- `doc/docs/architecture/tests/80_tests.dot`

Aucun SVG n'est inclus. Les SVG restent générés localement par le makefile.
