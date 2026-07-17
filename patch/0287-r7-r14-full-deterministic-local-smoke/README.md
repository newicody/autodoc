# 0287-r7-r14-full-deterministic-local-smoke

## Purpose

Close one deterministic local proof across the already implemented r7, r11,
r12 and r13 boundaries: three GitHub artifact members, intake and correlated
work package, explicit operator gate, two separately scheduled native
specialist visits, SQL authority, OpenVINO/E5-384 plus Qdrant recall, liaison
synthesis, final deliverable publication preview and exact simulated readback.

## Base

- required previous patch: `0287-r7-r13-final-deliverable-publication-plan`
- required path: `src/context/love_final_deliverable_publication_plan_0287.py`
- last public commit independently verified during preparation:
  `9d94f322bfeb81ad696855ab486daf3cf27dfc64` (`r12`)
- the exact commit SHA produced by applying r13 is intentionally not guessed

## Scope

- one asynchronous composition surface in `src/context`;
- exactly three artifact members: authoritative request, Copilot advisory and
  correlation manifest;
- explicit `promote` or `merge` SourceCandidate decision;
- one injected existing Scheduler used for two distinct visits;
- existing SQL, E5-384, Qdrant, evidence and liaison-synthesis surfaces reused;
- r13 Issue/ProjectV2 publication preview and exact local readback reused;
- no network client, remote mutation, new Scheduler, manager, queue, bus,
  registry, backend or dependency.

## Apply

Apply r13 first, then:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r14-full-deterministic-local-smoke \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0287-r7-r14-full-deterministic-local-smoke \
  --commit \
  --push \
  --allow-dirty
```

## Expected validation

```bash
python -m compileall -q src tests
python -m pytest -q \
  tests/context/test_love_full_deterministic_local_smoke_0287_r7_r14.py \
  tests/rules/test_love_full_deterministic_local_smoke_0287_r7_r14_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Suggested commit subject

```text
add full deterministic local smoke
```

## Next patch

`0287-r7-r15-real-github-actions-closed-loop-evidence`
