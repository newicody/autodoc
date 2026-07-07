# Phase 0171 test report

Planned validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_github_attachment_reference_fetch_contract_0171.py tests/tools/test_run_github_attachment_reference_fetch_once_0171.py tests/rules/test_github_attachment_reference_fetch_0171_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

Expected status: local fixture attachment fetch passes; no live GitHub dependency.
