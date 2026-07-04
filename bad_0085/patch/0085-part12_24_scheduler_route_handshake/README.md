# 0085-part12_24_scheduler_route_handshake

Phase 0085 : handshake côté Scheduler, sans service/daemon/CLI.

## Ajouts

```text
src/runtime/scheduler_route_handshake.py
doc/architecture/SCHEDULER_ROUTE_HANDSHAKE.md
doc/changelog/0085-scheduler-route-handshake.md
tests/test_scheduler_route_handshake.py
tests/rules/test_scheduler_route_handshake_rule.py
```

## Modifie

```text
doc/architecture/REAL_IMPLEMENTATION_SEQUENCE_0081.md
```

## Flow

```text
prepare_route_for_scheduler(...)
  -> tick_controlproxy(...)
  -> verify active route exists
  -> acquire route lease
  -> activate route lease
  -> publish handshake facts
  -> return route_handle + lease_id
```

## Idempotence

```text
same holder + same scope + active lease -> return existing lease
different holder/scope -> reject
closed lease -> reject
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0085-part12_24_scheduler_route_handshake

unzip -o /chemin/vers/${PATCH_ID}.zip -d .

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_scheduler_route_handshake.py \
  tests/test_controlproxy_pump.py \
  tests/test_controlproxy_route_lease.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Prochaine phase

0086 : adapter minimal du Scheduler existant vers `prepare_route_for_scheduler()`, toujours sans service.
