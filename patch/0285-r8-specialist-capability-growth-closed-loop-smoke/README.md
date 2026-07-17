# 0285-r8 — specialist capability growth closed-loop smoke

This additive patch closes the generic phase-0285 capability-growth path by
composing the existing r2-r7 contracts and the existing 0284-r5 portable
specialist laboratory smoke.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0285-r8-specialist-capability-growth-closed-loop-smoke \
  --commit \
  --push \
  --allow-dirty
```

## Boundaries

- requires the r2-r7 patches already applied;
- requires the existing 0284-r5 laboratory smoke;
- adds no Scheduler, registry, queue, EventBus, provider or durable store;
- requires an injected durable SQL-authoritative history port;
- leaves Qdrant non-authoritative and performs no GitHub mutation;
- does not modify `templates/github/projects-repository/INSTALLATION.md`.

## Focused validation

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_specialist_capability_growth_closed_loop_smoke_0285.py \
  tests/rules/test_specialist_capability_growth_closed_loop_smoke_0285_rule.py
```
