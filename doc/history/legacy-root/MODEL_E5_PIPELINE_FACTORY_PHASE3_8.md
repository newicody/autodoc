# Phase 3.8 — Factory de pipeline local E5

Cette phase transforme le test d'intégration réel multilingual-e5-small en capacité configurable.

## Objectif

Avant cette phase, le test réel assemblait manuellement :

```text
MultilingualE5SmallLocalConfig
  -> OpenVINOModelProfileRegistry
  -> TransformersAutoTokenizer
  -> TokenizerRegistry
  -> RealOpenVINORuntime
  -> OpenVINOBackendFactory
  -> BackendRegistry
  -> OpenVINOEmbeddingPipeline
```

La phase 3.8 regroupe cet assemblage dans `MultilingualE5SmallPipelineFactory`.

## Nouveau flux

```text
MultilingualE5SmallPipelineConfig
  -> MultilingualE5SmallPipelineFactory
  -> MultilingualE5SmallPipelineBundle
      -> OpenVINOEmbeddingPipeline
      -> OpenVINOModelProfileRegistry
      -> TokenizerRegistry
      -> BackendRegistry
      -> MultilingualE5SmallPipelineBuildSummary
```

## Règles conservées

- le Scheduler ne connaît pas le pipeline ;
- aucun téléchargement de modèle ;
- aucun fallback implicite vers un autre modèle ;
- `openvino` reste importé uniquement par `RealOpenVINORuntime` ;
- `transformers` reste importé uniquement dans l'adapter tokenizer local ;
- les tests unitaires injectent un runtime et un tokenizer factices ;
- le test réel reste optionnel via `MISSIPY_RUN_OPENVINO_LOCAL=1`.

## Usage local réel

```python
from inference.e5_pipeline import (
    MultilingualE5SmallPipelineConfig,
    build_multilingual_e5_small_pipeline,
)
from inference.e5_profile import MultilingualE5SmallLocalConfig

local = MultilingualE5SmallLocalConfig(
    model_dir="/home/eric/model/openvino/multilingual-e5-small",
)
bundle = build_multilingual_e5_small_pipeline(
    MultilingualE5SmallPipelineConfig(local=local, require_model_exists=True)
)
```

Puis :

```python
result = await bundle.pipeline.embed_text("query: exemple de recherche")
```

## Pourquoi c'est utile

Cette factory devient le point d'entrée propre pour activer le premier modèle réel sans disperser la configuration dans les tests ou dans le futur launcher.
