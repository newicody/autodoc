# 0287-r7-r15-r3-r11-r1-live-qdrant-projection-probe

Preview-first controlled probe for one SQL-authoritative analysis:

```text
PostgreSQL object + active revision
→ confirmed plan digest
→ OpenVINO E5 passage embedding
→ one named dense+sparse Qdrant point
→ SQL projection metadata
→ exact Qdrant readback without vectors
→ SQL source/projection rehydration
```

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r11-r1-live-qdrant-projection-probe \
  --dry-run \
  --allow-dirty
```

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r11-r1-live-qdrant-projection-probe \
  --commit \
  --push \
  --allow-dirty
```

## Preview after integration

Choose an existing SQL authority object and an accepted revision where that
object is an active member:

```bash
python tools/probe_love_live_qdrant_projection_0287.py \
  --config .var/config/love_installed_runtime.ini \
  --object-ref '<SQL_OBJECT_REF>' \
  --revision-ref '<CONTEXT_REVISION_REF>' \
  --branch-ref branch:main \
  --project-ref project:autodoc \
  --conversation-ref conversation:love-live-probe \
  --specialist-ref specialist:love-concept-affect \
  --laboratory-ref laboratory:love-studies \
  --security-scope security-scope:project \
  --policy-decision-id policy:love-live-projection-preview \
  --format json |
tee /tmp/love-live-projection-preview.json
```

Preview opens PostgreSQL for read-only authority checks. It does not construct
OpenVINO or a Qdrant client and performs no Qdrant mutation.

Execution is intentionally deferred until the preview returns `ready=true` and
an exact `plan_digest`.
