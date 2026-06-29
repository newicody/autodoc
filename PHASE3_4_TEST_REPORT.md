# Phase 3.4 — Test report

## Commandes exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

## Résultats

```text
compileall OK
109 passed in 1.23s
main.py exit code: 0
DOT_OK
```

## Notes

Le makefile Graphviz affiche encore l’avertissement connu :

```text
Warning: Orthogonal edges do not currently handle edge labels. Try using xlabels.
```

Cet avertissement n’empêche pas la génération des SVG et ne modifie pas les sources DOT.

## Portée de la phase

La Phase 3.4 ajoute le contrat tokenizer abstrait :

```text
TokenizationRequest
  -> TextTokenizer
  -> TokenizationResult
  -> OpenVINOEmbeddingRawInputs
```

Aucun import `transformers`, `tokenizers`, `sentencepiece` ou autre dépendance externe n'est ajouté.
