# Test report — Phase 2.9 — RealOpenVINORuntime isolé

## Commandes exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

## Résultats

```text
71 passed in 0.99s
main.py exit code: 0
DOT_OK
```

`make -f makefile` a régénéré les SVG dans le workspace de test pour valider les DOT, mais aucun SVG n'est inclus dans le lot de fichiers modifiés.

## Portée de la phase

Cette phase ajoute l'import OpenVINO réel uniquement dans :

```text
src/inference/openvino_runtime.py
```

Aucun autre module n'importe `openvino`.

## Limites assumées

Le runtime réel reste générique et attend des entrées OpenVINO brutes dans :

```python
InferenceRequest.context["inputs"]
```

ou :

```python
InferenceRequest.metadata["inputs"]
```

Il ne choisit aucun modèle, n'ajoute aucun tokenizer et ne fait pas de post-traitement spécifique embedding/generation.
