# Phase 3.1 — Factory OpenVINO depuis profils

## Objectif

La Phase 3.1 ajoute le pont contrôlé entre les profils déclaratifs OpenVINO et les backends réellement enregistrables.

La Phase 3.0 disait seulement :

```text
ce modèle pourrait exister
```

La Phase 3.1 permet maintenant :

```text
ce profil précis devient un OpenVINOBackend enregistrable
```

sans choisir de modèle par défaut, sans tokenizer et sans importer `openvino` dans la factory.

## Nouveau flux

```text
OpenVINOModelProfileRegistry
  -> select(profile_name)
  -> OpenVINOBackendFactory
  -> OpenVINOModelProfile.to_backend_config()
  -> runtime_factory(profile, config)
  -> OpenVINOBackend(config, runtime)
  -> BackendRegistry.register(backend)
```

## Rôles séparés

```text
OpenVINOModelProfileRegistry = inventaire déclaratif des modèles possibles
OpenVINOBackendFactory       = activation explicite d'un profil
BackendRegistry              = inventaire des backends exécutables
InferenceAdapter             = exécution via backend sélectionné
```

## Ce que la factory ne fait pas

```text
pas de fallback de modèle
pas de sélection automatique embedding/generation
pas de tokenizer
pas de post-processing
pas d'import openvino
pas de modification Scheduler
```

Le runtime est injecté par une fonction :

```text
runtime_factory(profile, config) -> OpenVINORuntime
```

Cela permet de tester avec un runtime factice, puis d'utiliser plus tard `RealOpenVINORuntime` sans changer le kernel.

## Multi-modèles

La factory permet d'enregistrer plusieurs profils :

```text
BackendRegistry
  ├── openvino.embedding.bge-m3
  ├── openvino.embedding.minilm
  └── openvino.generation.qwen
```

Le choix reste dans `InferenceRequest.model`.

## Décision maintenue

La recommandation reste de commencer par un profil `embedding`, mais le code ne l'impose pas.

La prochaine étape logique est d'ajouter un profil embedding réel local, puis de définir le format exact des entrées/sorties autour de ce modèle.
