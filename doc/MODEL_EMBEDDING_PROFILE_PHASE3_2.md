# Phase 3.2 — Profil embedding OpenVINO configurable

## Objectif

La Phase 3.2 ajoute la première spécialisation déclarative autour d'OpenVINO :
le profil `embedding`.

On ne branche toujours pas un modèle précis. Le code fournit une forme stable
pour dire :

```text
ce modèle local, choisi par l'utilisateur, doit être traité comme un modèle d'embedding OpenVINO
```

## Nouveau contrat

```text
OpenVINOEmbeddingProfileConfig
  -> model_path
  -> name = openvino.embedding
  -> device = CPU
  -> input_names
  -> output_names
  -> dimension optionnelle
  -> pooling déclaratif
  -> normalize déclaratif
  -> metadata
```

La configuration se convertit vers le contrat générique :

```text
OpenVINOEmbeddingProfileConfig
  -> to_model_profile()
  -> OpenVINOModelProfile(task="embedding")
```

## Pourquoi une config spécialisée alors qu'il existe déjà OpenVINOModelProfile ?

`OpenVINOModelProfile` est volontairement générique : il peut représenter un
modèle `embedding`, `generation` ou `raw`.

`OpenVINOEmbeddingProfileConfig` ajoute seulement le vocabulaire propre aux
embeddings :

```text
dimension
pooling
normalize
input_names/output_names typiques
```

Ces champs restent déclaratifs. Ils ne font pas encore de pré-traitement.

## Ce qui n'est pas fait

```text
pas de tokenizer
pas de conversion texte -> tokens
pas de pooling réel
pas de normalisation réelle
pas de Qdrant
pas de vérification de chemin modèle
pas de modèle imposé
```

Le runtime réel `RealOpenVINORuntime` attend encore des entrées brutes dans :

```text
InferenceRequest.context["inputs"]
```

ou :

```text
InferenceRequest.metadata["inputs"]
```

## Exemple de configuration Python

```python
from inference.embedding_profile import OpenVINOEmbeddingProfileConfig

config = OpenVINOEmbeddingProfileConfig(
    model_path="/chemin/vers/openvino_model.xml",
    name="openvino.embedding.local",
    device="GPU",
    dimension=1024,
    input_names=("input_ids", "attention_mask"),
    output_names=("embedding",),
    pooling="model",
    normalize=True,
)

profile = config.to_model_profile()
```

## Exemple de mapping configurable

```python
config = OpenVINOEmbeddingProfileConfig.from_mapping(
    {
        "model_path": "/chemin/vers/openvino_model.xml",
        "name": "openvino.embedding.local",
        "device": "CPU",
        "dimension": 768,
        "input_names": ["input_ids", "attention_mask"],
        "output_names": ["embedding"],
        "pooling": "model",
        "normalize": True,
    }
)
```

Cette forme est volontairement compatible avec une future configuration JSON,
TOML ou YAML sans ajouter de dépendance externe maintenant.

## Pooling déclaratif

Valeurs acceptées :

```text
model
cls
mean
none
```

En Phase 3.2, cette valeur est seulement mémorisée dans les métadonnées du
profil. L'exécution du pooling appartiendra à une phase ultérieure, quand le
pré-traitement/post-traitement embedding sera défini.

## Place dans l'architecture

```text
OpenVINOEmbeddingProfileConfig
  -> OpenVINOModelProfileRegistry
  -> OpenVINOBackendFactory
  -> BackendRegistry
  -> InferenceAdapter
```

Le Scheduler ne change pas.

## Décision stratégique

On confirme la recommandation : commencer par `embedding` avant `generation`.
Mais le code reste multi-profils : il n'empêche pas d'ajouter ensuite
`openvino.generation` ou plusieurs profils embedding concurrents.
