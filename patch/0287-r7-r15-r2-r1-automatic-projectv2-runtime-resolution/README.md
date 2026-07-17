# 0287-r7-r15-r2-r1 — automatic ProjectV2/runtime resolution

## Purpose

Correct the r15-r2 operator boundary. The imported-run preview now derives the
source Issue from the authoritative artifact and resolves the exact ProjectV2
item and field through the existing read-only GraphQL adapter.

The operator no longer has to discover or export `PROJECT_ITEM_ID` or
`PROJECT_FIELD_ID`, and no longer has to repeat the runtime-factory argument on
every run.

Preview remains mandatory and this command still cannot perform a remote
mutation.

## Base

Apply after:

```text
0287-r7-r15-r2-imported-actions-run-publication-preview
```

The patch also updates the cumulative installation guide already present under
`templates/github/projects-repository/INSTALLATION.md`.

## One-time local configuration

The command reuses by default:

```text
.var/config/github_project_v2_query_only.ini
```

for the ProjectV2 owner, project number and token environment name.

Create the local closed-loop configuration once:

```bash
mkdir -p .var/config

test -f .var/config/love_actions_closed_loop.ini || \
  cp config/love_actions_closed_loop.example.ini \
     .var/config/love_actions_closed_loop.ini
```

Then set the installation-owned real runtime factory:

```ini
[runtime]
factory = package.module:build_runtime
```

The factory must return the existing attested `ImportedActionsRuntimePorts`:
Scheduler, SQL authority, OpenVINO/E5-384 and Qdrant. The patch does not guess a
module, scan packages or install a dummy fallback.

An environment override is available for controlled tests:

```bash
export AUTODOC_LOVE_RUNTIME_FACTORY='package.module:build_runtime'
```

## Short preview command

```bash
python tools/run_love_actions_closed_loop_0287.py \
  --run-id "$RUN_ID" \
  --repository newicody/projects \
  --candidate-decision promote \
  --format text
```

The command now performs:

```text
three Actions artifacts
→ authoritative Issue number
→ configured ProjectV2 owner/number
→ exact read-only item/field resolution
→ attested r14 runtime composition
→ mandatory r15-r1 preview
→ /tmp/love-r14-result-<RUN_ID>.json
```

The resolved target is stored in `_r15_resolution` for audit.

For `--candidate-decision merge`, also pass the existing target context:

```text
--target-context-id <CONTEXT_ID>
```

Low-level options remain available only as diagnostic overrides:

```text
--project-owner
--project-number
--project-item-id
--project-field-ref
--project-field-name
--runtime-factory
```

If the Issue is not already present in the configured ProjectV2, the preview
fails closed. It does not silently add the Issue because that would be a remote
mutation before approval.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r1-automatic-projectv2-runtime-resolution \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r1-automatic-projectv2-runtime-resolution \
  --commit \
  --push \
  --allow-dirty
```

## Expected validation

```bash
python -m compileall -q src tools tests

python -m pytest -q \
  tests/context/test_love_actions_closed_loop_resolution_0287_r7_r15_r2_r1.py \
  tests/tools/test_run_love_actions_closed_loop_0287_r7_r15_r2.py \
  tests/rules/test_love_actions_closed_loop_resolution_0287_r7_r15_r2_r1_rule.py

python -m pytest -q tests/rules
python -m pytest -q
```

## Suggested commit subject

```text
simplify imported Actions preview resolution
```

## Next patch

`0287-r7-r15-r3` binds the explicit factory contract to the concrete installed
server composition, runs the mandatory live preview, performs the separately
approved publication, verifies Issue and ProjectV2 readback, and proves replay.
