# Changelog — Phase 2.9 — RealOpenVINORuntime isolé

## Objectif

Introduire le runtime OpenVINO réel sous forme isolée, sans choisir de modèle et sans modifier le Scheduler.

Cette phase est volontairement limitée : elle ajoute la capacité technique de charger/compiler/exécuter un modèle OpenVINO avec des entrées brutes, mais elle ne fournit pas encore de tokenizer, de profil embedding ou de profil génération.

## Ajouts

- `src/inference/openvino_runtime.py`
  - `RealOpenVINORuntime`
  - `RealOpenVINORuntimeState`
  - `RealOpenVINORuntimeError`
  - `RealOpenVINORuntimeUnavailable`
- `tests/inference/test_openvino_runtime.py`
  - runtime testé avec faux module OpenVINO injecté ;
  - cache de `CompiledModel` validé ;
  - erreur explicite si aucune entrée brute n'est fournie ;
  - absence d'OpenVINO installée acceptée en test.

## Modifications

- `src/inference/openvino_backend.py`
  - l'état du backend indique maintenant si le runtime injecté est un vrai runtime OpenVINO.
- `src/inference/__init__.py`
  - exporte les nouveaux symboles runtime.
- `doc/ARCHITECTURE_LAYERS.md`
  - état mis à jour vers Phase 2.9.
- `doc/OPENVINO_MODEL_STRATEGY.md`
  - précise que le runtime réel existe, mais reste raw-input only.
- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/inference/41_openvino_backend.dot`
- `doc/docs/architecture/inference/42_openvino_runtime.dot`
- `doc/docs/architecture/tests/80_tests.dot`

## Règles maintenues

- Aucun import OpenVINO dans le Scheduler.
- Aucun import OpenVINO dans `OpenVINOBackend`.
- Aucun modèle imposé.
- Aucun tokenizer ajouté.
- Aucune dépendance externe obligatoire pour lancer les tests ordinaires.
- L'import `openvino` est isolé dans `src/inference/openvino_runtime.py`.

## Limites assumées

`RealOpenVINORuntime` attend des entrées OpenVINO brutes dans :

```python
InferenceRequest.context["inputs"]
```

ou :

```python
InferenceRequest.metadata["inputs"]
```

Cela permet de tester le runtime sans décider encore si le premier modèle sera un embedding model, un modèle de génération ou plusieurs backends spécialisés.
