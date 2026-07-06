# 0075-part12_14_fake_runtime_replace_semantics

Correctif : semantics replace par defaut pour la fake runtime.

## Probleme

Ton run 0074 a montre :

```text
route_message_count = 6
record_count = 10
```

au lieu de :

```text
route_message_count = 3
record_count = 7
```

Cause : les fichiers `routes/<route_id>/messages.jsonl` etaient append entre runs.

## Correction

- `write_projection_to_fake_runtime(..., replace_routes=True)` par defaut.
- Supprime l'ancien dossier `routes/` avant de re-ecrire la projection.
- `FakeLocalRouteTransport.send` garde append semantics si utilise directement.
- `tools/write_baby_fork_fake_runtime.py` ajoute `--append-routes`.

## Non-objectifs

- Pas de vrai `/dev/shm`.
- Pas de semaphores.
- Pas de ring buffer.
- Pas de RouteProxy daemon.
- Pas de Scheduler wiring.
- Pas de ControlFS mutation.
- Pas de NetworkBridge.
- Pas de HardwareBridge.
- Pas de cluster.

## Prerequis

Appliquer avant :

```text
0063-r2
0064
0065
0066
0067
0068
0069
0071-0073
0074
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0075-part12_14_fake_runtime_replace_semantics

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate conseillee

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q \
  tests/test_fake_runtime_replace_semantics.py \
  tests/test_baby_fork_runtime_flow.py \
  tests/test_fake_route_transport.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Test apres application

```bash
PYTHONPATH=src:. python tools/run_baby_fork_runtime_flow.py \
  .var/baby_fork_smoke/baby_fork_report.json \
  .var/baby_fork_fake_runtime \
  .var/baby_fork_fake_runtime/runtime_journal.jsonl \
  --controlfs-root .var/baby_fork_controlfs
```

Attendu meme apres plusieurs runs :

```text
fake_runtime.route_message_count = 3
recorder.record_count = 7
```

## Prochaine phase recommandee

0076 : premier modele in-process ring buffer sans mmap.
