# Test report — Phase 1.3

## Workspace testé

Workspace local composé de la base Phase 1.2bis et des fichiers Phase 1.3.

## Commandes exécutées

```bash
python3 -m compileall -q src tests
pytest -q
python3 src/main.py
dot -Tsvg doc/docs/architecture/context/20_context.dot >/tmp/context.svg
dot -Tsvg doc/docs/architecture/scheduler/10_scheduler.dot >/tmp/scheduler.svg
```

## Résultat

```text
6 passed
MAIN_OK
DOT_OK
```

## Sortie main.py

```text
[Lifecycle] LOAD: DummyExpert -> scheduler payload=None
[Lifecycle] START: DummyExpert -> scheduler payload=None
[Tick] DummyExpert: 'hello'
[Lifecycle] STOP: DummyExpert -> scheduler payload=None
```

## Notes

Graphviz émet un avertissement non bloquant avec `splines=ortho` et les labels d'arêtes :

```text
Warning: Orthogonal edges do not currently handle edge labels. Try using xlabels.
```

Aucun SVG n'est fourni dans ce lot. Les SVG doivent être générés par le Makefile du dépôt.
