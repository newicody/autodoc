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

The next runtime changes require separate, explicit decisions. Current priority
order is:

```text
1. controlled real Qdrant executor, reusing the existing projection/recall surfaces
2. read-only real GitHub scan adapter, before any remote mutation gate
3. explicit remote GitHub mutation gate with operator approval, only after read-only validation
4. optional OpenRC service wrapper outside Scheduler, only if operationally necessary
5. specialist and distributed extensions after the durable/recall path is stable
```

Each item must begin with an audit of existing code. A new manager, orchestrator,
worker or adapter is forbidden when an existing surface can be extended.

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

The current GitHub intake starts from the user ProjectV2 configured in
`config/github_project_v2_query_only.example.ini`.  It is operated with Python
commands and that configuration file only; there is no installation script and
no Scheduler-owned service lifecycle.

First export the token named by `github.token_env` in the configuration:

```bash
export GITHUB_TOKEN='...'
```

Test the local files and safety boundaries without contacting GitHub:

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --format summary
```

Test the already-deployed ProjectV2 and GitHub Actions workflow through
query-only API calls:

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0272:deployment-readiness \
  --format summary
```

The readiness command does not install files, deploy a workflow, dispatch an
Action, write a secret, or mutate GitHub. The complete manual configuration,
including repository settings, token scope, Actions permissions and the
important distinction between ProjectV2 drafts and repository Issues, is in:

```text
doc/operator/GITHUB_PROJECT_ACTIONS_CONFIGURATION_0272.md
```

Before the live check can be green, the operator must have copied the existing
templates into the configured external repository:

```text
templates/github/autodoc-ticket-artifact.yml
  -> .github/workflows/autodoc-ticket-artifact.yml

templates/github/scripts/build_autodoc_ticket_artifact.py
  -> scripts/build_autodoc_ticket_artifact.py
```

The normal incoming flow is then launched explicitly:

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

ProjectV2 is the canonical GitHub read source. The Actions artifact workflow
is a separately verified secondary exchange path for real repository Issue
events; a ProjectV2 `DRAFT_ISSUE` is handled by the direct GraphQL snapshot and
does not trigger that workflow. Local snapshots, change sets and SourceCandidate
handoffs remain under local authority. R6 does not write SQL or Qdrant; every
handoff is held for the future operator gate.
