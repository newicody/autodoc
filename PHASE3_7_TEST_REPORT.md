# PHASE3_7_TEST_REPORT

## Validation réalisée dans ce sandbox

Le workspace complet du dépôt n'est pas présent dans `/mnt/data` pour cette phase. Je n'ai donc pas exécuté `pytest` sur toute la base locale depuis le sandbox.

Validation effectuée sur les fichiers Python ajoutés :

```bash
python3 -m py_compile \
  src/inference/transformers_tokenizer.py \
  src/inference/e5_profile.py \
  tests/inference/test_transformers_tokenizer_adapter.py \
  tests/inference/test_e5_profile.py \
  tests/integration/test_openvino_e5_local.py
```

Résultat :

```text
PY_COMPILE_OK
```

## Validation à lancer dans le dépôt local

Suite portable :

```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
python3 -m compileall -q src tests
pytest -q
```

Test réel OpenVINO local :

```bash
MISSIPY_RUN_OPENVINO_LOCAL=1 \
MISSIPY_E5_SMALL_DIR=/home/eric/model/openvino/multilingual-e5-small \
pytest -q tests/integration/test_openvino_e5_local.py
```

## Résultat attendu

- la suite normale doit passer sans lancer OpenVINO réel ;
- le test d'intégration doit être `skipped` sans `MISSIPY_RUN_OPENVINO_LOCAL=1` ;
- avec la variable activée et le modèle local présent, le pipeline doit produire un vecteur 384 normalisé.
