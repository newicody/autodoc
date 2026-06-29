# CHANGELOG — Phase 3.8 E5 Pipeline Factory

## Ajouté

- `src/inference/e5_pipeline.py`
  - `MultilingualE5SmallPipelineConfig`
  - `MultilingualE5SmallPipelineBuildSummary`
  - `MultilingualE5SmallPipelineBundle`
  - `MultilingualE5SmallPipelineFactory`
  - `build_multilingual_e5_small_pipeline()`

- `tests/inference/test_e5_pipeline_factory.py`
  - construction des registres avec runtime/tokenizer injectés ;
  - exécution du pipeline avec runtime factice ;
  - vérification de `require_model_exists=True`.

## Modifié

- `tests/integration/test_openvino_e5_local.py`
  - utilise maintenant la factory au lieu d'assembler manuellement le pipeline.

- `src/inference/__init__.py`
  - exporte les constantes E5, la config locale E5, le tokenizer Transformers optionnel et la factory E5.

- `README.md`
  - état de référence mis à jour jusqu'à la phase 3.8.

- `doc/ARCHITECTURE_LAYERS.md`
  - ajout de la couche factory locale E5.

## Non modifié

- Scheduler ;
- Dispatcher ;
- ComponentProxy ;
- PolicyEngine ;
- Qdrant ;
- génération texte ;
- graphes SVG.
