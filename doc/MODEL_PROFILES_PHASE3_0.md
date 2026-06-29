# Phase 3.0 — Profils déclaratifs OpenVINO

## Objectif

La Phase 3.0 introduit un registre de profils de modèles OpenVINO sans charger OpenVINO et sans choisir un modèle à la place de l'utilisateur.

Le problème à résoudre est simple : on ne sait pas encore si le prototype utilisera un modèle d'embedding, un modèle de génération, ou plusieurs modèles. Il faut donc représenter ce choix proprement avant de créer des backends exécutables.

## Nouveau contrat

```text
OpenVINOModelProfile
  -> name
  -> model_path
  -> task: embedding | generation | raw
  -> device
  -> input_names
  -> output_names
  -> metadata
```

Le profil est déclaratif. Il ne fait pas :

```text
import openvino
ov.Core()
tokenization
post-processing
Qdrant
création d'un backend réel
```

## Registre de profils

```text
OpenVINOModelProfileRegistry
  -> register(profile)
  -> select(name)
  -> by_task(task)
  -> snapshot()
```

Ce registre n'est pas `BackendRegistry`.

```text
OpenVINOModelProfileRegistry = liste des modèles possibles
BackendRegistry              = liste des moteurs exécutables disponibles
```

Cette distinction évite de mélanger la décision d'architecture avec l'exécution runtime.

## Pont vers le backend

Un profil peut produire une configuration de backend :

```text
OpenVINOModelProfile
  -> to_backend_config()
  -> OpenVINOBackendConfig
```

Ensuite seulement, une future phase pourra créer :

```text
OpenVINOBackend(config, RealOpenVINORuntime)
```

## Pourquoi c'est utile

Cette phase permet de préparer plusieurs chemins sans en choisir un arbitrairement :

```text
openvino.embedding
openvino.generation
openvino.raw
```

Le `Scheduler`, le `Dispatcher`, le `ComponentProxy`, le `InferenceRequestHandler` et le `InferenceAdapter` ne changent pas.

## Décision maintenue

La recommandation reste : commencer par `embedding` avant `generation`, mais le code ne force pas cette décision.

`embedding` est plus simple à valider et plus utile pour la future base de connaissance/Qdrant. `generation` demandera une phase séparée pour tokenizer, detokenizer, stratégie KV-cache et tests de stabilité.

## Extension Phase 3.1 — Factory de backend

La Phase 3.1 ajoute le pont manquant :

```text
OpenVINOModelProfile
  -> OpenVINOBackendFactory
  -> OpenVINOBackend
  -> BackendRegistry
```

Le profil reste déclaratif. La factory décide seulement de construire un backend depuis un profil explicite et un runtime injecté.

Cette séparation évite de confondre :

```text
modèle connu     = profil dans OpenVINOModelProfileRegistry
modèle actif     = backend enregistré dans BackendRegistry
modèle exécuté   = InferenceRequest.model sélectionné par InferenceAdapter
```

Aucun tokenizer n'est encore ajouté ici.
