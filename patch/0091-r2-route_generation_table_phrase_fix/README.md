# 0091-r2-route_generation_table_phrase_fix

Correctif minimal pour 0091-r2.

Le patch 0091-r2 contient bien l'intention opérationnelle, mais la phrase exacte
attendue par `tests/rules/test_route_generation_table_rule.py` n'apparaît pas en
un seul morceau dans le texte concaténé module + documentation.

Ce correctif ne change que deux formulations textuelles afin que la phrase exacte
suivante soit présente sans retour ligne :

```text
incremented only when a new route generation is materialized
```

## Scope

- No CLI.
- No OpenRC service and no resident daemon.
- No watcher.
- No Scheduler.run() modification.
- No live mmap resize.
- ControlProxy does not decide security.
- Scheduler/policy/zone remain the authority.
- No Qdrant, LLM, or OpenVINO path.
- No deletion of `__pycache__` or compiled files.

## Apply

```bash
python apply_patch_queue.py --patch 0091-r2-route_generation_table_phrase_fix --allow-dirty --dry-run
python apply_patch_queue.py --patch 0091-r2-route_generation_table_phrase_fix --allow-dirty --commit --push
```
