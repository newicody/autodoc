# 0146 — Artifact intake contract

Purpose: add a pure typed intake contract for local artifacts before dynamic route refs are derived.

This patch adds:

- `src/context/artifact_intake_contract.py`
- `artifact_intake_contract.json` output in `tools/run_local_artifact_vector_indexing_runner.py`
- CLI fields: `--artifact-ref`, `--artifact-kind`, `--text-kind`, `--vector-indexing-job-ref`

It reuses the existing 0145 runner and does not create a new orchestrator, Scheduler runner, OpenVINO adapter, or Qdrant adapter.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_artifact_intake_contract_0146.py tests/rules/test_artifact_intake_contract_0146_rule.py
```
