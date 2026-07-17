# 0287-r7-r15-r2-imported-actions-run-publication-preview

## Purpose

Add the missing producer for the r14 JSON consumed by the r15-r1 publisher.
The command imports one completed GitHub Actions run, downloads and validates
exactly the three correlated artifacts, executes the already-closed r14 path on
explicitly injected real runtime ports, writes
`/tmp/love-r14-result-<RUN_ID>.json`, and performs the mandatory r15-r1 remote
preview.

No Issue or ProjectV2 mutation is possible from the new command.

## Base

Apply after:

- `0287-r7-r14-full-deterministic-local-smoke`
- `0287-r7-r15-r1-final-deliverable-remote-publication-adapter`

Required paths include:

- `src/context/love_full_deterministic_local_smoke_0287.py`
- `src/context/love_final_deliverable_remote_publication_0287.py`
- `tools/publish_love_final_deliverable_0287.py`

## Important runtime boundary

This patch deliberately does **not** fabricate an OpenVINO/Qdrant proof and
does not ship a deployment-specific runtime manager. The command requires an
existing configured factory:

```text
--runtime-factory package.module:build_runtime
```

The factory must return `ImportedActionsRuntimePorts` carrying:

- the canonical existing Scheduler and dispatcher;
- the SQL authority and an existing base revision;
- real OpenVINO/E5-384 projection;
- real Qdrant write/search ports;
- the canonical collection, embedder and hybrid executor;
- an immutable backend attestation with evidence references.

There is no dummy or deterministic fallback. Until the server deployment
provides that factory, the command fails closed and writes no r14 result.

The Scheduler lifecycle must be explicit:

- `tool-bounded`: the command starts and stops one dedicated injected Scheduler;
- `externally-managed`: the server already owns the loop and the command never
  calls `run()` or `shutdown()`.

## Generate the r14 result and mandatory preview

Example for a promoted source candidate:

```bash
RUN_ID='<ACTIONS_RUN_ID>'

python tools/run_love_actions_closed_loop_0287.py \
  --run-id "$RUN_ID" \
  --repository newicody/projects \
  --candidate-decision promote \
  --runtime-factory '<configured.module>:build_runtime' \
  --project-item-id "$PROJECT_ITEM_ID" \
  --project-field-ref "$PROJECT_FIELD_ID" \
  --project-field-name 'Statut révision' \
  --project-status-value 'Terminé' \
  --output "/tmp/love-r14-result-$RUN_ID.json" \
  --format text
```

For `--candidate-decision merge`, also provide:

```text
--target-context-id <EXISTING_CONTEXT_ID>
```

The command:

1. validates a completed successful run;
2. requires exactly one request, advisory and manifest artifact from that run;
3. performs pure artifact/intake preflight before runtime initialization;
4. requires the explicit `promote` or `merge` operator decision;
5. executes r14 through the attested real runtime ports;
6. reads the Issue and ProjectV2 field through r15-r1;
7. performs the mandatory preview;
8. atomically writes the correlated JSON.

It has no `--execute` option.

## Inspect or repeat the preview

```bash
python tools/publish_love_final_deliverable_0287.py \
  --plan "/tmp/love-r14-result-$RUN_ID.json" \
  --operator-decision approve \
  --format json
```

A missing plan file now returns a concise operator-facing error instead of a
Python traceback.

## Controlled execution remains separate

After inspection, the existing r15-r1 command remains the only mutation
boundary. It still requires all three locks, `--execute`, and the exact preview
digest:

```bash
export AUTODOC_REMOTE_MUTATION_ALLOWED=true
export AUTODOC_ISSUE_PUBLICATION_ALLOWED=true
export AUTODOC_PROJECT_PROJECTION_ALLOWED=true

python tools/publish_love_final_deliverable_0287.py \
  --plan "/tmp/love-r14-result-$RUN_ID.json" \
  --operator-decision approve \
  --execute \
  --confirm-plan-digest '<EXACT_PLAN_DIGEST>' \
  --format json
```

Do not perform this live execution until r15-r3 has bound and verified the
concrete deployment factory and the preview has been reviewed.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-imported-actions-run-publication-preview \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-imported-actions-run-publication-preview \
  --commit \
  --push \
  --allow-dirty
```

## Expected validation

```bash
python -m compileall -q src tools tests
python -m pytest -q \
  tests/context/test_love_imported_actions_runtime_contract_0287_r7_r15_r2.py \
  tests/context/test_love_imported_actions_run_preview_0287_r7_r15_r2.py \
  tests/tools/test_run_love_actions_closed_loop_0287_r7_r15_r2.py \
  tests/rules/test_love_imported_actions_run_preview_0287_r7_r15_r2_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Suggested commit subject

```text
add imported Actions run publication preview
```

## Next patch

`0287-r7-r15-r3-live-issue-projectv2-closed-loop-evidence` binds this contract
to the concrete server runtime, performs and reviews the real preview, executes
with the exact digest, verifies remote readback, and proves idempotent replay.
