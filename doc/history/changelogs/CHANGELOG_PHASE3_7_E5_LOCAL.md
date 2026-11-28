# CHANGELOG — Phase 3.7 — E5 local optionnel

## Ajouté

- `src/inference/transformers_tokenizer.py`
  - adapter optionnel `TransformersAutoTokenizer` ;
  - import `transformers` isolé dans `from_pretrained()` ;
  - génération contrôlée de `token_type_ids` à zéro quand le tokenizer local ne les fournit pas.
- `src/inference/e5_profile.py`
  - profil local `openvino.embedding.e5-small` ;
  - entrée `input_ids`, `attention_mask`, `token_type_ids` ;
  - sortie `last_hidden_state` ;
  - dimension 384 ;
  - pooling `mean` ;
  - normalisation activée.
- Tests unitaires du tokenizer adapter et du profil E5.
- Test d'intégration OpenVINO local optionnel, désactivé par défaut.

## Important

Le test réel se lance uniquement avec :

```bash
MISSIPY_RUN_OPENVINO_LOCAL=1 \
MISSIPY_E5_SMALL_DIR=/home/eric/model/openvino/multilingual-e5-small \
pytest -q tests/integration/test_openvino_e5_local.py
```

## Non ajouté

- pas de téléchargement de modèle ;
- pas de dépendance obligatoire à `transformers` ;
- pas de Qdrant ;
- pas de batch embedding ;
- pas de génération texte.
