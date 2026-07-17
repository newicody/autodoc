# 0287-r7-r15-r1-final-deliverable-remote-publication-adapter

## Purpose

Add the controlled remote boundary that executes the exact immutable r13 final
deliverable publication plan against one GitHub Issue and one ProjectV2 field.
Preview remains the default. Execution requires explicit operator approval, the
three mutation locks and an exact `plan_digest`, followed by exact remote
readback through the r13 verifier.

This is the first unit of r15. It does not claim that a real Actions run has
already been executed or that live closed-loop evidence has been recorded.

## Base

- required previous patch: `0287-r7-r14-full-deterministic-local-smoke`
- required paths:
  - `src/context/love_final_deliverable_publication_plan_0287.py`
  - `src/context/love_full_deterministic_local_smoke_0287.py`
- last public commit independently verified during preparation:
  `9d94f322bfeb81ad696855ab486daf3cf27dfc64` (`r12`)
- r13 and r14 files are visible on `master`, but their exact resulting commit
  SHA is intentionally not guessed

## Scope

- transport-neutral command/result and Issue/ProjectV2 protocols in
  `src/context`;
- parser for exact r13 plan JSON or an r14 result carrying `publication_plan`;
- remote preflight reads and create/update/replay/collision decisions;
- explicit partial-execution result;
- thin GitHub CLI adapter for REST Issue comments and GraphQL ProjectV2;
- exact post-mutation Issue plus ProjectV2 readback;
- no Scheduler, laboratory, specialist, SQL, Qdrant or OpenVINO modification;
- no new dependency, manager, orchestrator, queue or registry.

## Preview

```bash
python tools/publish_love_final_deliverable_0287.py \
  --plan /tmp/love-r14-result.json \
  --operator-decision approve \
  --format json
```

## Controlled execution

Inspect the preview and copy its exact `plan_digest`, then open the three
boundaries explicitly:

```bash
export AUTODOC_REMOTE_MUTATION_ALLOWED=true
export AUTODOC_ISSUE_PUBLICATION_ALLOWED=true
export AUTODOC_PROJECT_PROJECTION_ALLOWED=true

python tools/publish_love_final_deliverable_0287.py \
  --plan /tmp/love-r14-result.json \
  --operator-decision approve \
  --execute \
  --confirm-plan-digest '<EXACT_PLAN_DIGEST>' \
  --format json
```

The default token source is `AUTODOC_PROJECT_TOKEN`; use `--token-env` to select
another environment variable already accepted by the local installation.

## Apply

Apply r14 first, then:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r1-final-deliverable-remote-publication-adapter \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0287-r7-r15-r1-final-deliverable-remote-publication-adapter \
  --commit \
  --push \
  --allow-dirty
```

## Expected validation

```bash
python -m compileall -q src tools tests
python -m pytest -q \
  tests/context/test_love_final_deliverable_remote_publication_0287_r7_r15_r1.py \
  tests/tools/test_publish_love_final_deliverable_0287_r7_r15_r1.py \
  tests/rules/test_love_final_deliverable_remote_publication_0287_r7_r15_r1_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Suggested commit subject

```text
add controlled final deliverable remote publication
```

## Next patches

- `0287-r7-r15-r2-imported-actions-run-publication-execution`
- `0287-r7-r15-r3-live-closed-loop-evidence`
- then `0287-r7-r16-recovery-installation-prototype-closure`
