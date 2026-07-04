# 0083-part12_22_controlproxy_route_lease_state

Phase 0083 : état de lease de route, sans daemon/service/CLI.

## Ajouts

```text
src/runtime/controlproxy_route_lease.py
doc/architecture/CONTROLPROXY_ROUTE_LEASE_STATE.md
doc/changelog/0083-controlproxy-route-lease-state.md
tests/test_controlproxy_route_lease.py
tests/rules/test_controlproxy_route_lease_rule.py
```

## Modifie

```text
doc/architecture/REAL_IMPLEMENTATION_SEQUENCE_0081.md
```

## État verrouillé

```text
not_leased -> leased -> active -> draining -> closed
leased -> closed
```

Fichiers :

```text
active/routes/<route_id>/lease.json
active/routes/<route_id>/status.json
```

## Important

Ce module enregistre l'état de lease. Il ne donne pas l'autorité sécurité.

```text
Security / policy / zone restent côté Scheduler/policy engine.
```

## Pas de CLI

```text
module logic is importable
tests validate behavior
CLI only when it is a real operator boundary
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0083-part12_22_controlproxy_route_lease_state

unzip -o /chemin/vers/${PATCH_ID}.zip -d .

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_controlproxy_route_lease.py \
  tests/test_route_notification.py \
  tests/test_controlproxy_active_routes.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Prochaine phase

0084 : ControlProxy pump/tick importable, pas service.
