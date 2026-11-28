# Phase 3.5 — Test report

## Scope

Phase 3.5 ajoute le pipeline embedding abstrait : tokenizer injectable -> raw inputs -> `InferenceAdapter` -> backend -> raw outputs -> vecteur embedding.

Aucun tokenizer concret, aucun modèle local et aucun Qdrant ne sont ajoutés.

## Commandes exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

## Résultat

```text
compileall OK
113 passed in 1.50s
main.py exit code: 0
DOT_OK
```

Les warnings Graphviz `Orthogonal edges do not currently handle edge labels` sont connus et ne bloquent pas la génération des SVG par le makefile.

## Tests ajoutés

```text
tests/inference/test_openvino_embedding_pipeline.py
```

Couverture ajoutée :

```text
OpenVINOEmbeddingPipelineConfig validation
OpenVINOEmbeddingPipelineResult immutability/metadata
pipeline mono-texte : tokenizer -> backend -> output adapter -> vector
refus batch Phase 3.5
refus backend sans raw_outputs
RealOpenVINORuntime expose metadata['raw_outputs']
```
