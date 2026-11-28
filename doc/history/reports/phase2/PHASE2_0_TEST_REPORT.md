# Phase 2.0 — Test report

## Commandes exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
```

## Résultat pytest

```text
35 passed in 0.36s
```

## Résultat main

```text
main.py exit code: 0
[Lifecycle] LOAD: DummyExpert -> scheduler payload=None
[Lifecycle] START: DummyExpert -> scheduler payload=None
[Tick] DummyExpert: 'hello'
[Lifecycle] STOP: DummyExpert -> scheduler payload=None
```

## Validation DOT

Fichiers vérifiés avec Graphviz :

```text
doc/docs/architecture/00_global.dot
doc/docs/architecture/observability/70_observability.dot
doc/docs/architecture/tests/80_tests.dot
```

Résultat :

```text
DOT_OK
```

## Portée

La Phase 2.0 ajoute un `ReplaySandbox` minimal.

Le sandbox reste isolé :

- pas de connaissance du Scheduler ;
- pas de publication d'événements ;
- pas de reconstruction de `Request.reply` ;
- pas de désérialisation automatique de `payload_repr` ;
- refus de `SHUTDOWN` par défaut.
