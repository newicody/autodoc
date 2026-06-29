# Manifest — Phase 2.6

## Objet

Contrat `OpenVINOBackend` sans runtime OpenVINO réel.

Cette phase prépare directement l'intégration OpenVINO, mais n'importe pas encore
`openvino` et ne modifie pas le Scheduler, le Dispatcher ou le ComponentProxy.

## Fichiers modifiés

```text
src/inference/openvino_backend.py
src/inference/__init__.py
tests/inference/test_openvino_backend_contract.py

doc/ARCHITECTURE_LAYERS.md
doc/CHANGELOG_PHASE2_6.md

doc/docs/architecture/inference/40_inference.dot
doc/docs/architecture/inference/41_openvino_backend.dot
doc/docs/architecture/tests/80_tests.dot
```

## Non inclus

```text
aucun SVG
aucun script de patch
aucun fichier runtime OpenVINO réel
aucune modification Scheduler/Dispatcher/ComponentProxy
```
