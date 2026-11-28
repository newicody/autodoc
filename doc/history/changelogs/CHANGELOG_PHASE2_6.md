# Changelog — Phase 2.6

## Objectif

Préparer l'intégration OpenVINO sans importer le runtime OpenVINO réel.

Cette phase ajoute un backend contractuel testable avec runtime injecté. Le
Scheduler, le Dispatcher, le ComponentProxy et le chemin Event restent inchangés.

## Ajouté

- `src/inference/openvino_backend.py`
  - `OpenVINOBackendConfig`
  - `OpenVINOBackendState`
  - `OpenVINOBackendError`
  - `OpenVINORuntime`
  - `OpenVINOBackend`
- Exports dans `src/inference/__init__.py`.
- Tests `tests/inference/test_openvino_backend_contract.py`.
- Graphe détaillé `doc/docs/architecture/inference/41_openvino_backend.dot`.

## Modifié

- `doc/ARCHITECTURE_LAYERS.md`
- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/tests/80_tests.dot`

## Garanties

- Aucun import de `openvino`.
- Aucun changement dans le Scheduler.
- Aucun changement dans le Dispatcher.
- Aucun changement dans le ComponentProxy.
- Aucun enregistrement OpenVINO dans le Launcher.
- Le backend OpenVINO reste testable avec un faux runtime injecté.
- Les DOT gardent une navigation cohérente vers le nouveau niveau de détail.

## Validation

```text
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```
