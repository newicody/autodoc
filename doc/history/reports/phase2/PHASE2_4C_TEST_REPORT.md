# Test report — Phase 2.4c

## Commandes exécutées

```bash
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py
PYTHONPATH=src pytest -q
```

## Résultats

```text
3 passed in tests/docs/test_dot_links.py
54 passed in full test suite
```

## Notes

- Le test ne force plus de page canonique globale.
- Le test ne force plus la bidirection parent -> enfant.
- Le test vérifie seulement que les liens internes Graphviz pointent vers une source DOT existante sous `doc/docs/architecture`.
- Les DOT plats hérités du scheduler sont transformés en redirections vers les sous-graphes détaillés.
