# 0077-part12_16_route_message_frame_codec

Phase 0077 : codec de frame byte-level pour RouteMessage.

## Objectif

Verifier la transformation :

```text
RouteMessage
-> payload canonique bytes
-> frame binaire
-> decode
-> RouteMessage valide
```

## Ajouts

- `src/runtime/route_frame_codec.py`
- `tools/roundtrip_route_frame.py`
- `doc/architecture/ROUTE_MESSAGE_FRAME_CODEC.md`
- `doc/changelog/0077-route-message-frame-codec.md`
- `tests/test_route_frame_codec.py`
- `tests/rules/test_route_message_frame_codec_rule.py`

## Header v1

```text
magic          8 bytes
version        uint16
flags          uint16
header_size    uint32
payload_size   uint32
payload_sha256 32 bytes
```

## Verifications au decode

```text
magic
version
header size
frame length
payload SHA-256
RouteMessage schema
```

## Non-objectifs

- Pas de vrai `/dev/shm`.
- Pas de mmap.
- Pas de semaphores.
- Pas de eventfd/futex.
- Pas de ring buffer implementation.
- Pas de RouteProxy daemon.
- Pas de watcher ControlFS.
- Pas de wiring Scheduler.
- Pas de zero-copy transport.
- Pas de NetworkBridge.
- Pas de HardwareBridge.
- Pas de cluster.

## Prerequis

Appliquer avant tous les patchs jusqu'a :

```text
0076-part12_15_inprocess_ring_buffer_model
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0077-part12_16_route_message_frame_codec

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate conseillee

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. pytest -q   tests/test_route_frame_codec.py   tests/test_inprocess_ring_buffer.py   tests/test_fake_runtime_replace_semantics.py

PYTHONPATH=src:. pytest -q tests/rules
```

## Test CLI apres application

Produire la fake runtime :

```bash
PYTHONPATH=src:. python tools/run_baby_fork_runtime_flow.py   .var/baby_fork_smoke/baby_fork_report.json   .var/baby_fork_fake_runtime   .var/baby_fork_fake_runtime/runtime_journal.jsonl   --controlfs-root .var/baby_fork_controlfs
```

Roundtrip frame :

```bash
PYTHONPATH=src:. python tools/roundtrip_route_frame.py   .var/baby_fork_fake_runtime   --route-id baby_fork.variant_stub
```

Attendu :

```text
frame_count = 1
route_id = baby_fork.variant_stub
payload_sha256 = sha256:...
```

## Prochaine phase recommandee

0078 : integrer le frame codec dans le ring in-process.
