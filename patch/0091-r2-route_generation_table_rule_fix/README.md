# 0091-r2 route generation table rule fix

Correctif minimal à appliquer après l'échec de `0091-r2-route_generation_table`.

Objectifs :

- garder la phrase exacte attendue par `tests/rules/test_route_generation_table_rule.py` sur une seule ligne : `incremented only when a new route generation is materialized` ;
- supprimer les fichiers `__pycache__/*.pyc` qui avaient été inclus par erreur dans le patch 0091-r2 ;
- ne pas modifier le Scheduler, la PriorityQueue, le Dispatcher, ni le contrat Component tick/yield/reply ;
- ne pas ajouter de CLI, service OpenRC, daemon, watcher, backend, Qdrant, LLM ou OpenVINO.

Application sur l'état dirty laissé par l'échec précédent :

```bash
unzip -o /mnt/data/0091-r2-route_generation_table_rule_fix.zip -d .
python apply_patch_queue.py --patch 0091-r2-route_generation_table_rule_fix --allow-dirty --dry-run
python apply_patch_queue.py --patch 0091-r2-route_generation_table_rule_fix --allow-dirty --commit --push
```

Validation ciblée :

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/rules/test_route_generation_table_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
