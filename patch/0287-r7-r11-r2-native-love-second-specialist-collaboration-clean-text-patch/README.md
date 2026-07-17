# 0287-r7-r11-r2 — clean text-only collaboration patch

This patch replaces both failed r11 bundles:

- `0287-r7-r11-native-love-second-specialist-collaboration`;
- `0287-r7-r11-r1-native-love-second-specialist-collaboration-rebase`.

The functional r11 implementation is unchanged. This revision is rebuilt from a
clean baseline and stages only the ten intended text files. It contains no
`__pycache__`, `.pyc`, `.pyo`, binary patch marker or binary diff.

The patch activates the second love-domain specialist through a second visit
submitted to the existing Scheduler. The first analysis becomes one canonical,
digest-backed artifact and one v2 completion message. The second specialist
performs its own relational-dynamics analysis and closes the ordered two-visit
conversation. Global synthesis remains r12 work.

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
- no SQL, Qdrant, OpenVINO, ControlProxy or GitHub effect;
- no direct specialist-to-specialist invocation;
- no global synthesis;
- `INSTALLATION.md` is unchanged.
