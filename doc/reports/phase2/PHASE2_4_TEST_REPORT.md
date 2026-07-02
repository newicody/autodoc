# Phase 2.4 — Rapport de test

Commandes exécutées :

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
for f in $(find doc/docs/architecture -name '*.dot' -print | sort); do dot -Tsvg "$f" >/dev/null; done
```

Résultat :

```text
52 passed in 0.41s
main.py exit code: 0
DOT_OK
```

Note Graphviz : `splines=ortho` peut avertir sur les labels d'arêtes. Ce n'est pas bloquant et ne concerne pas la validité des liens.
