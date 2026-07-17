# 0287-r7-r13-final-deliverable-publication-plan

## Purpose

Close the pure publication-planning boundary after the r12
`FinalArtifactEnvelope`. The patch renders a deterministic final Issue document,
creates a marker distinct from Copilot advisory comments, prepares one concise
ProjectV2 projection, computes one exact combined `plan_digest`, and defines
exact dual-surface readback verification.

## Base

- expected base commit: `9d94f322bfeb81ad696855ab486daf3cf27dfc64`
- previous completed step: `0287-r7-r12-love-memory-evidence-liaison-synthesis`

## Scope

- one pure stdlib publication contract;
- immutable typed command, plan, operation, projection and readback results;
- Issue create/replay/collision planning;
- ProjectV2 update/replay planning;
- no network call or remote mutation;
- no Scheduler, ControlProxy, SQL, Qdrant, OpenVINO or installation changes.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r13-final-deliverable-publication-plan \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0287-r7-r13-final-deliverable-publication-plan \
  --commit \
  --push \
  --allow-dirty
```

## Expected validation

```bash
python -m compileall -q src tests
python -m pytest -q \
  tests/context/test_love_final_deliverable_publication_plan_0287_r7_r13.py \
  tests/rules/test_love_final_deliverable_publication_plan_0287_r7_r13_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Suggested commit subject

```text
add final deliverable publication plan
```

## Next patch

`0287-r7-r14-full-deterministic-local-smoke`
