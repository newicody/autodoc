# Phase 1.9 — Test report

## Commandes exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
```

## Résultat pytest

```text
29 passed in 0.31s
```

## Résultat main.py

```text
[Lifecycle] LOAD: DummyExpert -> scheduler payload=None
[Lifecycle] START: DummyExpert -> scheduler payload=None
[Tick] DummyExpert: 'hello'
[Lifecycle] STOP: DummyExpert -> scheduler payload=None
```

## DOT

Syntaxe Graphviz validée pour :

- `doc/docs/architecture/00_global.dot`
- `doc/docs/architecture/observability/70_observability.dot`
- `doc/docs/architecture/tests/80_tests.dot`

Avertissement connu non bloquant :

```text
Warning: Orthogonal edges do not currently handle edge labels. Try using xlabels.
```
