# Phase 3.7b — rapport de test

## Contexte

Correction ciblée suite au test réel local :

```bash
MISSIPY_RUN_OPENVINO_LOCAL=1 \
MISSIPY_E5_SMALL_DIR=/home/eric/model/openvino/multilingual-e5-small \
pytest -q tests/integration/test_openvino_e5_local.py
```

L'échec venait de l'envoi d'un `mappingproxy` à OpenVINO.

## Validation effectuée ici

Le sandbox ne contient pas le dépôt complet ni le modèle local OpenVINO.
La validation exécutée ici porte donc sur la syntaxe des fichiers ajoutés :

```bash
python3 -m py_compile src/inference/openvino_runtime.py
python3 -m py_compile tests/inference/test_openvino_runtime.py
```

Résultat : `PY_COMPILE_OK`.

## Validation à lancer localement

```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
python3 -m compileall -q src tests
pytest -q

MISSIPY_RUN_OPENVINO_LOCAL=1 \
MISSIPY_E5_SMALL_DIR=/home/eric/model/openvino/multilingual-e5-small \
pytest -q tests/integration/test_openvino_e5_local.py
```
