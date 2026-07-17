# 0287-r7-r7 — correlated research work package

Builds one deterministic, read-only research package from the validated 0281
run assembly, 0275 intake, Issue attachment manifest and attachment fetch
report.

The package preserves the authoritative request and optional Copilot advisory
in their original public schemas. Fetched attachments cross the contract only
as server-dataset references and SHA-256 digests; raw bytes and local paths are
not exposed.

Prerequisites:

- `0287-r7-r5-product-final-specialist-exchange-synthesis-reuse-audit`;
- `0287-r7-r6-copilot-advisory-v2-board-issue-publication`;
- `0287-r7-r6-r1-copilot-v2-installation-budget-correction`.

Validation:

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_correlated_research_work_package_0287.py \
  tests/rules/test_correlated_research_work_package_0287_rule.py
```

This phase performs no IO, Scheduler route, laboratory execution, SQL/Qdrant
write or GitHub mutation. `INSTALLATION.md` is intentionally unchanged.
