# 0069-part12_11_fake_runtime_recorder_ingestion

Phase 0069 : ingestion Recorder depuis fake runtime.

## Objectif

Lire la surface fake runtime :

```text
data.index.jsonl
event.bus.jsonl
context.bus.jsonl
routes/<route_id>/messages.jsonl
```

et produire un journal JSONL :

```text
runtime_journal.jsonl
```

Chaque ligne est un record :

```text
missipy.recorder.runtime_journal_record.v1
```

## Ajouts

- `src/runtime/fake_runtime_recorder.py`
- `tools/record_fake_runtime.py`
- `doc/architecture/FAKE_RUNTIME_RECORDER_INGESTION.md`
- `doc/changelog/0069-fake-runtime-recorder-ingestion.md`
- `tests/test_fake_runtime_recorder.py`
- `tests/rules/test_fake_runtime_recorder_ingestion_rule.py`

## Non-objectifs

- Pas de vrai `/dev/shm`.
- Pas de semaphores.
- Pas de ring buffer.
- Pas de daemon Recorder.
- Pas de wiring Scheduler.
- Pas de daemon RouteProxy.
- Pas de mutation ControlFS.
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
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0069-part12_11_fake_runtime_recorder_ingestion

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate conseillee

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_fake_route_transport.py \
  tests/test_fake_runtime_recorder.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Test CLI complet

```bash
PYTHONPATH=src:. python tools/write_baby_fork_fake_runtime.py \
  .var/baby_fork_smoke/baby_fork_report.json \
  .var/baby_fork_fake_runtime

PYTHONPATH=src:. python tools/record_fake_runtime.py \
  .var/baby_fork_fake_runtime \
  .var/baby_fork_fake_runtime/runtime_journal.jsonl

wc -l .var/baby_fork_fake_runtime/runtime_journal.jsonl
head -n 3 .var/baby_fork_fake_runtime/runtime_journal.jsonl
```

Attendu baby-fork actuel :

```text
7 records
```

## Prochaine phase recommandee

0070 : ajouter une option au CLI baby-fork pour produire directement fake runtime + recorder journal, ou générer les manifests ControlFS desired pour les routes baby-fork.
