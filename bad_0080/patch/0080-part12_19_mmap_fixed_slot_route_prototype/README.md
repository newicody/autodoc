# 0080-part12_19_mmap_fixed_slot_route_prototype

Phase 0080 : prototype `mmap fixed-slot`.

## Scope

Consomme une decision ControlProxy `ready` issue de `0079-r2/r3` et materialise :

```text
<runtime_root>/routes/<route_handle>/ring.bin
<runtime_root>/routes/<route_handle>/status.json
```

## Ajouts

```text
src/runtime/mmap_fixed_slot_route.py
doc/architecture/MMAP_FIXED_SLOT_ROUTE.md
doc/changelog/0080-mmap-fixed-slot-route-prototype.md
tests/test_mmap_fixed_slot_route.py
tests/rules/test_mmap_fixed_slot_route_rule.py
```

## Pas de nouveau CLI

Ce patch respecte la regle :

```text
module logic is importable
tests validate behavior
CLI only when it is a real operator boundary
```

## Non-objectifs

```text
pas de POSIX shm_open
pas de /dev/shm obligatoire
pas de semaphore/eventfd/futex
pas de daemon ControlProxy
pas de watcher ControlFS
pas de wiring Scheduler
pas de lease handoff
pas de live resize
pas d'inter-process safety
pas de VisPy renderer
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0080-part12_19_mmap_fixed_slot_route_prototype

unzip -o /chemin/vers/${PATCH_ID}.zip -d .

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_mmap_fixed_slot_route.py \
  tests/test_controlproxy_sizing_prepare.py \
  tests/test_inprocess_frame_ring.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Ce que le test prouve

```text
ControlProxy decision
-> ring.bin file-backed mmap
-> fixed slot frame write
-> fixed slot frame drain
-> decode RouteMessage frame
```

## Prochaine phase

0081 : materialiser `active/routes/<route_handle>/status.json` depuis la route mmap et preparer le handoff de lease.
