# 0287-r7-r10 — native love laboratory and first specialist

Prerequisite:

```text
0287-r7-r9-love-study-contracts-specialist-descriptors
```

This patch:

- promotes `laboratory:love-studies-local` to a ready native provider;
- appends its immutable registration to the existing Scheduler-owned registry;
- reuses `LABORATORY_VISIT_REQUEST` and the existing Dispatcher surface;
- executes the first content-dependent specialist;
- supports evidence extraction, concept analysis, affect mapping and explicit
  local synthesis;
- creates no Scheduler, queue, EventBus, registry manager, SQL/Qdrant authority,
  ControlProxy or GitHub mutation path.

Apply from the Autodoc repository root with `apply_patch_queue.py`.
