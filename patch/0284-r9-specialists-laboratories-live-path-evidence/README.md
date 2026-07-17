# 0284-r9 — specialists/laboratories live-path evidence

This patch adds the immutable evidence boundary recommended by 0284-r8.
It validates the JSON projection of one already executed 0284-r7 integrated
smoke, derives `Phase0284OperationalEvidence`, and reuses the existing r8
closure audit.

It adds no Scheduler, laboratory manager, backend adapter, transport or remote
mutation path. The verifier has no `--execute` option.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0284-r9-specialists-laboratories-live-path-evidence \
  --dry-run \
  --allow-dirty
```

After a green dry-run:

```bash
python apply_patch_queue.py \
  --patch 0284-r9-specialists-laboratories-live-path-evidence \
  --commit \
  --push \
  --allow-dirty
```

## Targeted checks

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_specialists_laboratories_live_path_evidence_0284.py \
  tests/rules/test_specialists_laboratories_live_path_evidence_0284_rule.py
```

Expected delivery result: `9 passed`.

## Operational verification

The cumulative Projects guide contains the command:

```text
templates/github/projects-repository/INSTALLATION.md
```

A real green r9 report requires a saved JSON result from an explicitly
authorised 0284-r7 execution. Unit tests validate the contract but do not claim
that the local SQL/OpenVINO/Qdrant path has already been executed.

Suggested commit:

```text
verify-specialists-laboratories-live-path-evidence
```
