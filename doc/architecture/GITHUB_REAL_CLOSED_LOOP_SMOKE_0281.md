# GitHub real closed-loop smoke — 0281-r7

## Purpose

Close the real local walking skeleton from one downloaded GitHub Actions run:

```text
authoritative request + Copilot advisory + manifest
-> 0281-r2 run assembly
-> 0275 intake
-> explicit operator promote decision
-> 0281-r5 advisory projection
-> existing platform Scheduler
-> 0274 fake laboratory SQL/projection/recall closure
-> publication_preview.json
-> 0281-r6 create/replay/collision publication plan
```

The smoke does not publish. The existing r6 tool remains the only Issue
mutation adapter and still requires an exact operator-confirmed plan digest.

## Real input

Download the successful run into one directory:

```bash
gh run download 29246131317   --repo newicody/projects   --dir .var/staging/github_closed_loop_0281/29246131317
```

The collector recognizes these basenames recursively:

```text
authoritative_request.json
copilot_advisory.json
dual_artifact_manifest.json
```

The r2/0275 contracts validate all references and SHA-256 digests before the
laboratory path runs.

## Existing Scheduler

The CLI starts the existing platform `kernel.scheduler.Scheduler` only as the
standalone process entrypoint, registers the existing laboratory visit handler,
and injects it into the r5/0274 path.

It does not define or instantiate a laboratory-local Scheduler, manager,
orchestrator, queue, bus or registry. The same kernel Scheduler implementation
remains the sole orchestration authority.

## Runtime adapters

The real smoke reuses the already-existing deterministic local adapters used by
the 0274 closed-loop tests:

```text
SQLiteSqlContextStore
DemoQdrantProjectionExecutor
DemoQdrantRecallExecutor
deterministic 384-dimensional embedding mapping
EventBus observation
```

This is a real integration smoke over the existing code path, not a claim that
the production Qdrant/OpenVINO adapters are deployed.

## Outputs

The tool writes an idempotent proof directory:

```text
.var/reports/github_closed_loop_0281/
  newicody__projects/<run_id>/
    closed_loop_result.json
    run_assembly.json
    laboratory_projection.json
    publication_preview.json
    publication_plan.json
```

An identical rerun is accepted as replay. A different result cannot silently
overwrite an existing proof.

## Repository impact

```text
newicody/autodoc: modification required
newicody/projects: no Git-tracked modification required
projects_repository_change_required: false
```

The external workflow already produced the three required artifacts. No
workflow or Actions permission change is needed.
