# 0287-r7-r11-r1 — native love second-specialist collaboration rebase

This patch replaces the failed `0287-r7-r11-native-love-second-specialist-collaboration`
bundle. The functional implementation is unchanged. Only the documentation diff
has been rebased on the current `doc/README_CURRENT.md` after r8-r1 through r10.

The patch activates `specialist:love-relational-dynamics-analyst` inside the
existing native love laboratory while preserving the r10 first-specialist-only
provider as historical evidence.

The first analysis becomes a canonical digest-backed artifact and a v2
completion message. The second task and continuation visit are prepared without
execution and must be submitted again through the existing Scheduler. The second
specialist produces its own content-dependent relational analysis and closes one
ordered two-visit conversation. Global synthesis remains r12 work.

## Prerequisite

`0287-r7-r10-native-love-laboratory-first-specialist`

## Validation

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_native_love_laboratory_second_specialist_0287_r7_r11.py \
  tests/rules/test_native_love_laboratory_second_specialist_0287_r7_r11_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Boundaries

- no Scheduler, queue, EventBus, registry manager or laboratory manager added;
- the existing r10 Scheduler-owned registration is upgraded in place;
- no SQL/Qdrant/OpenVINO/ControlProxy/GitHub effect;
- no direct specialist-to-specialist invocation;
- no global synthesis;
- `INSTALLATION.md` is unchanged.
