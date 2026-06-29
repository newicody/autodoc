# PHASE1.8 TEST REPORT

## Commandes exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
```

## Résultat

```text
25 passed in 0.39s
main.py exit code: 0
```

## Validation DOT

```bash
dot -Tsvg doc/docs/architecture/00_global.dot >/tmp/00_global.svg
dot -Tsvg doc/docs/architecture/observability/70_observability.dot >/tmp/70_observability.svg
dot -Tsvg doc/docs/architecture/tests/80_tests.dot >/tmp/80_tests.svg
```

Résultat : syntaxe DOT valide.

Graphviz affiche uniquement l'avertissement connu sur `splines=ortho` avec labels d'arêtes. Aucun SVG n'est fourni dans ce lot.
