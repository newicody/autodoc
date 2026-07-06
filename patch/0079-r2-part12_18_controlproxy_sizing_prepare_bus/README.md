# 0079-r2-part12_18_controlproxy_sizing_prepare_bus

Ce patch remplace l'ancien `0079` non applique.

Il repart de `0078` et integre directement les choix valides :

```text
ControlProxy = ControlFS + RouteProxy
```

## Contenu

- sizing hints dans les manifests ControlProxy/ControlFS
- pre-trame `required_frame_bytes`
- decision ControlProxy par zone/policy
- publication `event.bus` + `context.bus`
- audit repository avant mmap
- index architecture a jour

## Ajouts / modifications

```text
src/runtime/controlfs_manifest.py
src/runtime/controlproxy_prepare.py
src/context/baby_fork_controlfs.py
src/context/baby_fork_runtime_flow.py
tools/write_baby_fork_controlproxy_sized.py
tools/prepare_fake_routes_controlproxy.py
doc/architecture/CONTROLPROXY_SIZING_PREPARE_PROTOCOL.md
doc/architecture/REPOSITORY_ARCHITECTURE_AUDIT_0079_R2.md
doc/architecture/ARCHITECTURE_INDEX_0079_R2.md
doc/changelog/0079-r2-controlproxy-sizing-prepare-bus.md
tests/test_controlproxy_sizing_prepare.py
tests/test_baby_fork_runtime_flow_controlproxy_sizing.py
tests/test_controlproxy_prepare_cli.py
tests/rules/test_controlproxy_sizing_prepare_rule.py
```

## Important

Ne pas appliquer l'ancien `0079`.

Ne pas appliquer l'ancien `0080`.

Appliquer ce `0079-r2` apres `0078`.

## Application

```bash
cd ~/projet/git/autodoc

PATCH_ID=0079-r2-part12_18_controlproxy_sizing_prepare_bus

unzip -o /chemin/vers/${PATCH_ID}.zip -d .

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_controlproxy_sizing_prepare.py \
  tests/test_baby_fork_runtime_flow_controlproxy_sizing.py \
  tests/test_controlproxy_prepare_cli.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Test CLI

```bash
PYTHONPATH=src:. python tools/run_baby_fork_runtime_flow.py \
  .var/baby_fork_smoke/baby_fork_report.json \
  .var/baby_fork_fake_runtime \
  .var/baby_fork_fake_runtime/runtime_journal.jsonl \
  --controlfs-root .var/baby_fork_controlfs
```

Puis :

```bash
PYTHONPATH=src:. python tools/prepare_fake_routes_controlproxy.py \
  .var/baby_fork_fake_runtime \
  --task-id ctx-baby-fork-001 \
  --replace-bus
```

Attendu :

```text
request_count = 3
decision_count = 3
status = ready
action = create_route_generation
```

## Prochaine phase

`0080` devient maintenant :

```text
file-backed fixed-slot mmap route prototype
```
