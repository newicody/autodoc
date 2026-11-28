# Phase 1.5 — Test report

Workspace validé avec les fichiers Phase 1.5 complets.

## Commandes exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
```

## Résultat

```text
12 passed in 0.27s
main.py exit code: 0
```

## DOT

Syntaxe Graphviz validée sur :

- `doc/docs/architecture/00_global.dot`
- `doc/docs/architecture/scheduler/10_scheduler.dot`
- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/tests/80_tests.dot`

Aucun SVG n'a été inclus dans le lot.

## Note

Graphviz affiche l'avertissement connu suivant avec `splines=ortho` et des labels d'arêtes :

```text
Warning: Orthogonal edges do not currently handle edge labels. Try using xlabels.
```

Cet avertissement n'empêche pas la génération via le Makefile.
