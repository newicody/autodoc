# 0086-part12_25_scheduler_route_adapter

Phase 0086 : adapter minimal du Scheduler existant vers `prepare_route_for_scheduler()`.

## Ajouts

```text
src/runtime/scheduler_route_adapter.py
doc/architecture/SCHEDULER_ROUTE_ADAPTER.md
doc/changelog/0086-scheduler-route-adapter.md
tests/test_scheduler_route_adapter.py
tests/rules/test_scheduler_route_adapter_rule.py
```

## Modifie

```text
doc/architecture/REAL_IMPLEMENTATION_SEQUENCE_0081.md
```

## Flow

```text
SchedulerRouteRequest
  -> verify authorized=True and policy_decision_id exists
  -> prepare_route_for_scheduler(...)
  -> SchedulerRouteReply
  -> publish adapter facts to event.bus/context.bus
```

## Limite sécurité

```text
authorized=True + policy_decision_id obligatoire
mais aucune décision PolicyEngine ici
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0086-part12_25_scheduler_route_adapter

unzip -o /chemin/vers/${PATCH_ID}.zip -d .

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_scheduler_route_adapter.py \
  tests/test_scheduler_route_handshake.py \
  tests/test_controlproxy_pump.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Prochaine phase

0087 : connecter un handler Scheduler concret sans changer le loop.
