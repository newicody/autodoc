# 0081-part12_20_controlproxy_active_route_materializer

Phase 0081 : materialiseur de route active ControlProxy.

## Objectif

Prevoir l'implementation reelle en reliant maintenant :

```text
ControlProxy RoutePrepareDecision
+ desired RouteManifest
-> mmap route files
-> ControlFS active/routes/<route_id>/manifest.json
-> ControlFS active/routes/<route_id>/status.json
```

## Ajouts

```text
src/runtime/controlproxy_active_routes.py
doc/architecture/CONTROLPROXY_ACTIVE_ROUTE_MATERIALIZER.md
doc/architecture/REAL_IMPLEMENTATION_SEQUENCE_0081.md
doc/changelog/0081-controlproxy-active-route-materializer.md
tests/test_controlproxy_active_routes.py
tests/rules/test_controlproxy_active_routes_rule.py
```

## Pas de nouveau CLI

Le patch garde la regle :

```text
module logic is importable
tests validate behavior
CLI only when it is a real operator boundary
```

## Ce que le test prouve

```text
decision ControlProxy ready
-> mmap ring.bin/status.json
-> active/routes/<route_id>/manifest.json
-> active/routes/<route_id>/status.json
-> RouteProxy plan peut voir noop
-> la route mmap accepte et draine une frame
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0081-part12_20_controlproxy_active_route_materializer

unzip -o /chemin/vers/${PATCH_ID}.zip -d .

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_controlproxy_active_routes.py \
  tests/test_mmap_fixed_slot_route.py \
  tests/test_controlproxy_sizing_prepare.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Prochaine phase

0082 : notification primitive (`eventfd` ou semaphore abstraction) toujours sans daemon complet.
