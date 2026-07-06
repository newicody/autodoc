# 0084-part12_23_controlproxy_pump_tick

Phase 0084 : ControlProxy pump/tick importable, pas service.

## Ajouts

```text
src/runtime/controlproxy_pump.py
doc/architecture/CONTROLPROXY_PUMP_TICK.md
doc/changelog/0084-controlproxy-pump-tick.md
tests/test_controlproxy_pump.py
tests/rules/test_controlproxy_pump_rule.py
```

## Modifie

```text
doc/architecture/REAL_IMPLEMENTATION_SEQUENCE_0081.md
```

## Ce que fait un tick

```text
read ControlFS desired/active routes
build RouteProxy dry-run plan
materialize missing desired routes
write mmap route files
write ControlFS active route state
publish event.bus/context.bus facts
return structured result
```

## Ce que le tick refuse

```text
live mmap resize
implicit update of active route
delete/drain cleanup
lease issuing
security policy decision
Scheduler call
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0084-part12_23_controlproxy_pump_tick

unzip -o /chemin/vers/${PATCH_ID}.zip -d .

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_controlproxy_pump.py \
  tests/test_controlproxy_route_lease.py \
  tests/test_route_notification.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Prochaine phase

0085 : fonctions de handshake Scheduler-facing qui appellent le pump puis acquierent le lease, toujours sans service.
