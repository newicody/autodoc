# Test report — Phase 2.6

## Commandes exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

## Résultat

```text
63 passed in 0.66s
main.py exit code: 0
DOT_OK
```

## Notes

- Le test OpenVINO utilise `FakeOpenVINORuntime`.
- Aucun import de `openvino` n'est réalisé.
- Les warnings Graphviz `splines=ortho` avec labels d'arêtes restent non bloquants.
