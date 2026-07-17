# 0287-r7-r9 — love-study contracts and specialist descriptors

This patch declares the domain contracts, one disabled native laboratory and
two portable extensible multitask specialists. It remains contract-only.

## Prerequisite

- `0287-r7-r8-r6-authorized-context-impact-execution`

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r9-love-study-contracts-specialist-descriptors \
  --dry-run \
  --allow-dirty
```

After a green dry-run:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r9-love-study-contracts-specialist-descriptors \
  --commit \
  --push \
  --allow-dirty
```

## Boundaries

- Scheduler remains the only orchestration authority.
- SQL remains the durable context authority.
- Qdrant remains projection and recall only.
- OpenVINO is reused and not reimplemented.
- ControlProxy remains transport-only.
- No provider, handler, runtime or Scheduler registration is attached in r9.
- Global synthesis remains a later liaison step.
- `INSTALLATION.md` was reviewed and is unchanged.
