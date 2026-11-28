# Phase 3.3 — Test report

## Objet

Validation de la couche embedding raw : tokens déjà préparés vers entrées OpenVINO brutes, puis sortie brute vers vecteur embedding stable.

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
100 passed in 0.96s
main.py exit code: 0
DOT_OK
```

## Notes

Graphviz affiche quelques avertissements connus :

```text
Warning: Orthogonal edges do not currently handle edge labels. Try using xlabels.
```

Ces avertissements ne bloquent pas la génération et ne concernent pas la validité des sources DOT.

## Couverture ajoutée

- `OpenVINOEmbeddingRawInputs`
  - conversion depuis mapping JSON-like ;
  - validation des formes ;
  - validation `attention_mask` ;
  - projection vers `InferenceRequest.context["inputs"]`.
- `OpenVINOEmbeddingOutputAdapter`
  - sortie modèle déjà vectorielle ;
  - pooling `cls` ;
  - pooling `mean` avec `attention_mask` ;
  - normalisation L2 ;
  - erreurs sur sorties ambiguës ou vecteur nul.
- `OpenVINOEmbeddingVector`
  - dimension ;
  - norme L2 ;
  - validation valeurs finies.
