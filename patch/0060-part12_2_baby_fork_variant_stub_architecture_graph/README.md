# 0060 — Part 12.2 Baby Fork Variant Stub Architecture Graph

This patch corrects the 0059 wording and graph.

## Apply

```bash
python apply_patch_queue.py --patch 0060-part12_2_baby_fork_variant_stub_architecture_graph --dry-run
python apply_patch_queue.py --patch 0060-part12_2_baby_fork_variant_stub_architecture_graph --commit --push
```

## Scope

- Rename the fake MVTC step to `VariantGeneratorStub`.
- Correct the second baby-fork variant classification.
- Make the Cell Lens source class honest: `variant_generator.stub`.
- Add an architecture DOT graph separating current smoke flow from future MVTC/Scheduler/EventBus/Qdrant runtime.

## Out of scope

- No real MVTC implementation.
- No Qdrant dependency.
- No real Scheduler runtime.
- No EventBus runtime.
