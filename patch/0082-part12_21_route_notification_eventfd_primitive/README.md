# 0082-part12_21_route_notification_eventfd_primitive

Phase 0082 : primitive de notification reelle, sans daemon, sans service, sans nouveau CLI.

## Choix

Backend auto :

```text
1. Python os.eventfd si disponible
2. libc eventfd via ctypes sinon
3. pipe non-bloquant en fallback
```

Donc on exploite une primitive existante du kernel/libc, mais depuis Python.

## Ajouts

```text
src/runtime/route_notification.py
doc/architecture/ROUTE_NOTIFICATION_PRIMITIVE.md
doc/changelog/0082-route-notification-eventfd-primitive.md
tests/test_route_notification.py
tests/rules/test_route_notification_rule.py
```

## Modifications

```text
doc/architecture/REAL_IMPLEMENTATION_SEQUENCE_0081.md
doc/architecture/CONTROLPROXY_ACTIVE_ROUTE_MATERIALIZER.md
tests/rules/test_controlproxy_active_routes_rule.py
```

Correction de trajectoire :

```text
0084 != service
0084 = ControlProxy pump/tick importable, appele explicitement
```

## Ce que le test prouve

```text
mmap route write
-> notifier.notify(1)
-> selector voit fileno() readable
-> notifier.drain()
-> mmap route drain
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0082-part12_21_route_notification_eventfd_primitive

unzip -o /chemin/vers/${PATCH_ID}.zip -d .

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_route_notification.py \
  tests/test_controlproxy_active_routes.py \
  tests/test_mmap_fixed_slot_route.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Prochaine phase

0083 : etat de lease de route, sans daemon.
