# Phase 1.2bis — Test report

## Scope

Remise en conformité avec `doc/code-rules/code_rule.md` et correction des écarts visibles dans le dépôt courant.

## Commands executed

```bash
python3 -m compileall -q src tests
pytest -q
python3 src/main.py
```

## Result

```text
7 passed in 0.22s
MAIN_OK
```

## DOT validation

```bash
dot -Tsvg doc/docs/architecture/00_global.dot >/dev/null
dot -Tsvg doc/docs/architecture/scheduler/10_scheduler.dot >/dev/null
dot -Tsvg doc/docs/architecture/context/20_context.dot >/dev/null
```

Result: `DOT_OK`.

Graphviz warning observed on orthogonal edge labels; it is cosmetic and already known for `splines=ortho`.
