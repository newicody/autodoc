# Changelog — Phase 3.0 model profiles

## Ajouté

- `src/inference/model_profile.py`
  - `SUPPORTED_OPENVINO_TASKS`
  - `OpenVINOModelProfile`
  - `OpenVINOModelProfileRegistry`
  - `OpenVINOModelProfileRegistrySnapshot`
- `tests/inference/test_openvino_model_profile.py`
- `doc/MODEL_PROFILES_PHASE3_0.md`
- `doc/docs/architecture/inference/43_openvino_profiles.dot`
- `pytest.ini`

## Modifié

- `src/inference/__init__.py`
- `README.md`
- `doc/ARCHITECTURE_LAYERS.md`
- `doc/OPENVINO_MODEL_STRATEGY.md`
- `doc/docs/architecture/00_global.dot`
- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/inference/41_openvino_backend.dot`
- `doc/docs/architecture/inference/42_openvino_runtime.dot`
- `doc/docs/architecture/tests/80_tests.dot`

## Décision

La Phase 3.0 ne choisit pas encore un modèle OpenVINO précis. Elle ajoute une couche de description déclarative permettant de préparer un ou plusieurs modèles avant de créer les backends exécutables.

`BackendRegistry` reste le registre des backends exécutables. `OpenVINOModelProfileRegistry` est seulement le registre des modèles possibles.

## Garanties

- Aucun import `openvino` ajouté hors `src/inference/openvino_runtime.py`.
- Aucun changement du Scheduler.
- Aucun changement du Dispatcher.
- Aucun changement du ComponentProxy.
- Aucun tokenizer imposé.
- Aucun modèle local imposé.
- Aucun SVG inclus.
