# 0074-part12_13_baby_fork_runtime_flow_cli

Phase 0074 : CLI end-to-end baby-fork runtime flow.

## Objectif

Ajouter une commande qui enchaine :

```text
baby_fork_report.json
-> runtime projection
-> fake runtime surface
-> recorder journal
-> optional ControlFS desired manifests
-> optional RouteProxy dry-run plan
```

## Ajouts

- `src/context/baby_fork_runtime_flow.py`
- `tools/run_baby_fork_runtime_flow.py`
- `doc/architecture/BABY_FORK_RUNTIME_FLOW_CLI.md`
- `doc/changelog/0074-baby-fork-runtime-flow-cli.md`
- `tests/test_baby_fork_runtime_flow.py`
- `tests/rules/test_baby_fork_runtime_flow_cli_rule.py`

## Non-objectifs

- Pas de vrai Scheduler.
- Pas de daemon RouteProxy.
- Pas de vrai `/dev/shm`.
- Pas de semaphores.
- Pas de ring buffer.
- Pas de creation active/routes.
- Pas de mutation revoked/routes.
- Pas d'exigence ZFS.
- Pas de NetworkBridge.
- Pas de HardwareBridge.
- Pas de cluster.

## Prerequis

Appliquer avant :

```text
0063-r2-part12_5_controlfs_manifest_schema_validator
0064-part12_6_routeproxy_dry_run_reconciler
0065-part12_7_shm_runtime_message_schemas
0066-part12_8_baby_fork_runtime_message_projection
0067-part12_9_baby_fork_projection_report_compat
0068-part12_10_fake_local_route_transport
0069-part12_11_fake_runtime_recorder_ingestion
0071-0073-part12_12_controlfs_babyfork_routeproxy_shm_design
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0074-part12_13_baby_fork_runtime_flow_cli

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate conseillee

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_baby_fork_runtime_flow.py \
  tests/test_baby_fork_controlfs.py \
  tests/test_fake_runtime_recorder.py

PYTHONPATH=src:. pytest -q tests/rules
```

## CLI complet

```bash
PYTHONPATH=src:. python tools/run_baby_fork_runtime_flow.py \
  .var/baby_fork_smoke/baby_fork_report.json \
  .var/baby_fork_fake_runtime \
  .var/baby_fork_fake_runtime/runtime_journal.jsonl \
  --controlfs-root .var/baby_fork_controlfs
```

Attendu :

```text
projection.route_message_count = 3
recorder.record_count = 7
controlfs.action_counts.create = 3
```

## Prochaine phase recommandee

0075 : premier modele in-process ring buffer sans mmap.
