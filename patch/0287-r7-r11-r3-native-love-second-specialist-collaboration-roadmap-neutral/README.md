# 0287-r7-r11-r3 — roadmap-neutral clean collaboration patch

This patch replaces all previous failed r11 bundles.

The functional r11 implementation is unchanged. This revision:

- contains only nine intended text additions;
- does not modify `doc/README_CURRENT.md`;
- relies on the existing r11/r12 roadmap markers already present there;
- records the detailed r11 closure in the phase report, architecture, changelog
  and manifest;
- contains no `__pycache__`, `.pyc`, `.pyo`, binary marker or binary diff.

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
