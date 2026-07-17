# 0284-r2 — portable specialist contract

This patch adds the first-class immutable portable-specialist contract selected
by the 0284-r1 reuse audit.

## Scope

- stable specialist identity across multiple laboratories;
- declared capabilities and accepted/produced contracts;
- bounded execution preferences;
- positive laboratory compatibility and visit modes;
- pure validation against the shared route/visit reference vocabulary;
- no provider, handler, registry, Scheduler, EventBus, SQL, Qdrant, OpenVINO or
  GitHub effect.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0284-r2-portable-specialist-contract \
  --commit \
  --push \
  --allow-dirty
```

## Suggested commit

```text
add-portable-specialist-contract
```

## Next

```text
0284-r3-specialist-laboratory-message-contract
```
