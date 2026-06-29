# Changelog — Phase 3.1 Backend factory

## Ajouté

- `src/inference/openvino_factory.py`
  - `OpenVINOBackendFactory`
  - `OpenVINOBackendBuildResult`
  - `OpenVINORuntimeFactory`
- `tests/inference/test_openvino_backend_factory.py`
- `doc/MODEL_FACTORY_PHASE3_1.md`

## Modifié

- `src/inference/__init__.py`
- `README.md`
- `doc/ARCHITECTURE_LAYERS.md`
- `doc/OPENVINO_MODEL_STRATEGY.md`
- `doc/MODEL_PROFILES_PHASE3_0.md`
- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/inference/41_openvino_backend.dot`
- `doc/docs/architecture/inference/43_openvino_profiles.dot`
- `doc/docs/architecture/tests/80_tests.dot`

## Décision

La factory transforme un profil explicitement sélectionné en backend enregistrable. Elle ne choisit pas de modèle par défaut et n'importe pas `openvino`.

## Validation attendue

```text
compileall OK
pytest OK
main.py OK
DOT OK
```
