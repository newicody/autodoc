# 0287-r7-r8 — specialist message v2 and deep analysis

Adds explicit companion v2 contracts for specialist/laboratory exchanges while
preserving `missipy.specialist.laboratory_message.v1` unchanged.

The v2 boundary adds digest-backed artifacts, canonical payload digests,
correlation/idempotency identities, cross-visit continuation, normalized
completion/error messages and conversations spanning specialists. It also adds
request, finding and contribution contracts for deep domain analysis. Rich
analysis is preserved for the existing later liaison synthesis; global
synthesis is never inferred unless the mission requests it.

Prerequisite:

- `0287-r7-r7-correlated-research-work-package`.

Validation:

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_specialist_laboratory_message_v2_0287.py \
  tests/context/test_specialist_deep_analysis_contract_0287.py \
  tests/rules/test_specialist_message_v2_deep_analysis_0287_rule.py
```

This phase creates no Scheduler route, transport, laboratory runtime, durable
write, OpenVINO/Qdrant call or GitHub mutation. `INSTALLATION.md` is unchanged.
