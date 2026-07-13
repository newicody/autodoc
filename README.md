# Autodoc / MissiPy

Autodoc / MissiPy is a local-first engineering workspace for turning files,
notes, artifacts and operator decisions into explicit, auditable context.

The project is built around a simple rule:

```text
the local machine is the source of truth;
external services are workflow surfaces, not the authority.
```

## Why this exists

The goal is to build a small but strict context engine that can ingest candidate
sources, review them, decide what to do with them, audit those decisions and
prepare controlled handoffs.

This is useful when a human operator wants to keep ownership of the evolving
knowledge base while still using automation, local inference and external review
surfaces. Autodoc / MissiPy is local, inspectable and progressively extensible;
it is not designed as a remote-first agent.

## Current architecture

### Current operational baseline

The current production-prototype smoke is a controlled, one-shot composition of
existing phase tools:

```text
0260 SQL write
-> 0261 SQL rehydrate + OpenVINO/E5 embedding
-> 0262 Qdrant projection with payload.sql_ref
-> 0263 Qdrant recall refs + SQL rehydrate
-> 0264 closed ResultFrame
-> 0265 EventBus observation-only facts
-> 0266 PassiveSupervisor read model
-> 0267 local GitHub scan-once handoff
-> 0268 OpenRC/launcher readiness
-> 0269 production prototype smoke report
```

The validated boundary is:

```text
Scheduler = Autodoc orchestration authority
SQL = durable authority
Qdrant = projection and recall only
OpenVINO/E5 = explicit vector generation
EventBus = observation only
PassiveSupervisor = observation only
GitHub = review/workflow surface
OpenRC / OS / admin = external process authority
```

The 0269 execution path uses real SQL and real OpenVINO/E5. The current Qdrant
executor remains an explicit demonstration gate until a controlled real executor
is selected and validated. No phase in this baseline starts PostgreSQL, Qdrant or
OpenVINO daemons.

## Source of truth

The local/server machine remains authoritative. GitHub, future project trackers
and other external systems are projection, review and synchronization surfaces.
They may receive derived artifacts, status or operator-facing summaries, but they
do not own the evolving local context.

```text
local/server = authoritative evolving source
external surfaces = review, workflow and synchronization interfaces
```

## Patch queue workflow

Development is organized as small patch queue bundles under `patch/<patch-id>/`.
A patch bundle contains:

```text
patch/<patch-id>/
  patch.diff
  README.md
  metadata.json
```

Typical usage:

```bash
python apply_patch_queue.py --patch <patch-id> --dry-run --allow-dirty
python apply_patch_queue.py --patch <patch-id> --commit --push --allow-dirty
```

Before generating or applying a new patch, capture the exact checkout state:

```bash
git status --short
git log --oneline -5
git diff
```

Generated or local-only files such as SVG renders, Python bytecode, reports and
local patch queue configuration must not be versioned unless a phase manifest
explicitly requires them.

## Tests

Common gates:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

Specific phase tests and smoke commands are recorded in the corresponding phase
test reports.

## Documentation map

Use these documents as the current map:

```text
doc/architecture/CURRENT_ARCHITECTURE_STATE_0154.md
doc/architecture/OPERATIONAL_DOCUMENTATION_CONSOLIDATION_0270.md
doc/README_CURRENT.md
doc/ARCHITECTURE_LAYERS.md
doc/docs/architecture/00_global.dot
doc/code-rules/code_rule.md
```

Historical phase documents remain implementation evidence. They do not override
the current-state index or the 0270 operational decisions.

The root README is intentionally stable. It is an entrypoint, not a phase
changelog.

## AI-assisted development

This project is developed with help from several AI systems, including ChatGPT,
Claude, Gemini, Perplexity and Mistral.

That is a practical choice: the project is intentionally designed to run on
accessible local hardware, without requiring an expensive dedicated GPU. The
current direction favors CPU/iGPU-friendly components, local artifacts, explicit
contracts and controlled handoffs over blind dependence on high-end accelerator
hardware.

AI assistance is used to design, review and verify the system while keeping the
operational architecture local-first, inspectable and hardware-conscious.

## Current boundary

The project currently avoids:

```text
remote mutation by default
network dependency in local gates
GitHub API writes
tokens committed to the repository
implicit Qdrant durable authority
hidden OpenVINO execution inside Scheduler
Scheduler-owned external service lifecycle
```

External systems must be approached through explicit contracts, dry-runs,
reports and gates. GitHub remote mutation remains forbidden in the validated
0260-0269 baseline. Scheduler.run is not modified by the 0270 documentation
consolidation.

## Roadmap orientation

The active roadmap is maintained in `doc/README_CURRENT.md`. The immediate
walking-skeleton objective is to complete the existing GitHub dual-artifact path:

```text
GitHub Issue
-> authoritative request + Copilot advisory + correlation manifest
-> read-only local run assembly and 0275 intake
-> explicit operator decision
-> existing-Scheduler fake laboratory
-> controlled, idempotent publication
```

The Copilot CLI runtime must also be pinned and cached so repeated Actions runs
do not reinstall the complete npm dependency tree. Copilot output remains a
non-authoritative hint. Each item begins with an audit of existing code. A new
manager, orchestrator, worker, scheduler, queue, bus or registry is forbidden
when an existing surface can be extended.

## Non-goals

Autodoc / MissiPy is not currently:

```text
a hosted SaaS
a remote-first agent
a GitHub bot with write access by default
a replacement for human operator review
a hidden background daemon
a system that stores secrets in Git
a Scheduler-owned service manager
```

The project grows by small, auditable patches and explicit gates.

## GitHub ProjectV2 operator path

The current intake is **Project-native**. It reads the user ProjectV2 configured
in `config/github_project_v2_query_only.example.ini` directly through GraphQL
query-only calls. A separate repository and GitHub Actions workflow are not
required for ProjectV2 `DRAFT_ISSUE` items.

```text
GitHub ProjectV2 newicody/2
-> query-only snapshot
-> local snapshot diff
-> SourceCandidate handoff batch
-> explicit local operator gate
```

There is no installation script, deployment script or Scheduler-owned service
lifecycle. Export the token named by `github.token_env`:

```bash
export GITHUB_TOKEN='...'
```

### 1. Test the Project-native system

Local safety/readiness check without network access:

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --format summary
```

Live query-only ProjectV2 check:

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0272:project-native-readiness \
  --format summary
```

With the default configuration, `system_ready=True` requires the local Python
surfaces and the expected ProjectV2 identity. It does **not** require an external
Issues repository or an Actions workflow.

### 2. Run the inbound ProjectV2 chain

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_v2_query_only_snapshot_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0272:project-v2-query-only \
  --format summary

PYTHONPATH=src:. python \
  tools/detect_github_project_v2_snapshot_changes_0272.py \
  --execute \
  --policy-decision-id policy:0272:project-v2-change-detection \
  --format summary

PYTHONPATH=src:. python \
  tools/build_github_project_v2_change_handoffs_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0272:project-v2-change-handoff \
  --format summary
```

The first r4 run may be a baseline. After a Project item changes, rerun snapshot,
diff and handoff creation. The r6 summary gives a candidate count; the immutable
handoff batch is written under `.var/github/project_v2/handoffs/`.

### 3. Apply one explicit candidate decision

Inspect a handoff batch JSON to obtain a `candidate_id`, then apply one existing
`SourceCandidate` decision:

```bash
PYTHONPATH=src:. python \
  tools/gate_github_project_v2_source_candidate_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --candidate-id ghpv2-... \
  --action promote \
  --reason "accepted for durable local ingestion" \
  --execute \
  --policy-decision-id policy:0272:source-candidate-gate \
  --format summary
```

Allowed decisions are `inspect`, `relaunch`, `reject`, `archive`, `promote` and
`merge`. `merge` also requires `--target-context-id`. Only `promote` and `merge`
open a future durable-ingestion authorization; r7 itself still performs no SQL
write or Qdrant projection. Removed Project items remain advisory and cannot be
promoted or merged.

### Optional repository-Issue Actions bridge

The existing Actions template is a secondary path for real `issues` events in
an external repository. It is not part of the required Project-native setup and
it does not run for a ProjectV2-only draft.

To verify an already deployed optional bridge, add:

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --check-actions-bridge \
  --policy-decision-id policy:0272:actions-bridge-readiness \
  --format summary
```

This command only reads GitHub state. It does not copy a workflow, dispatch an
Action, create a repository, install a service, commit, push or mutate GitHub.
The optional bridge procedure and the Project-native distinction are documented
in `doc/operator/GITHUB_PROJECT_ACTIONS_CONFIGURATION_0272.md`.

Local snapshots, change sets, handoffs and decision records remain under local
authority. GitHub is the workflow/review surface; SQL and Qdrant remain closed
until the next accepted-ingestion phase.
