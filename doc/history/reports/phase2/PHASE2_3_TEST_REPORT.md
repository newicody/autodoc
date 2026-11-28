# Phase 2.3 — Test report

Commandes exécutées :

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

Résultat attendu :

```text
47 passed
main.py exit code: 0
DOT_OK
```
