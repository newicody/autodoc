# Phase 2.2 — Test Report

## Commandes exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
```

## Résultats

```text
42 passed in 0.36s
main.py exit code: 0
```

Sortie `main.py` :

```text
[Lifecycle] LOAD: DummyExpert -> scheduler payload=None
[Lifecycle] START: DummyExpert -> scheduler payload=None
[Tick] DummyExpert: 'hello'
[Lifecycle] STOP: DummyExpert -> scheduler payload=None
```

## Validation DOT

```bash
dot -Tsvg doc/docs/architecture/00_global.dot -o /tmp/00_global.svg
dot -Tsvg doc/docs/architecture/observability/70_observability.dot -o /tmp/70_observability.svg
dot -Tsvg doc/docs/architecture/tests/80_tests.dot -o /tmp/80_tests.svg
```

Résultat :

```text
DOT_OK
```

Graphviz peut émettre l'avertissement habituel sur `splines=ortho` et les labels d'arêtes ; ce n'est pas bloquant.
