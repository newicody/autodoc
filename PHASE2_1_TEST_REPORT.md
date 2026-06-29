# PHASE 2.1 — TEST REPORT

## Commandes exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

## Résultat

```text
39 passed in 0.36s
main.py exit code: 0
DOT_OK
```

Graphviz peut afficher l'avertissement connu sur `splines=ortho` avec labels d'arêtes. Cet avertissement n'empêche pas la génération des graphes.

## Couverture ajoutée

```text
tests/observability/test_replay_scenario.py
```

Les tests vérifient :

- génération d'un `ReplayReport` ;
- agrégation des compteurs ;
- handlers de simulation partagés ;
- sortie textuelle déterministe ;
- validation du nom de scénario ;
- validation du budget `max_events`.
