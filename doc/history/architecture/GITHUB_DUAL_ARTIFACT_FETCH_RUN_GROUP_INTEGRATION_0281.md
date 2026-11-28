# GitHub dual-artifact fetch run-group integration — 0281-r3

## Decision

The existing 0168 fetcher already exposes an explicit `--sync-tool` port.
This phase reuses that port instead of creating another fetcher or modifying
the network adapter.

The new sync adapter performs this composition:

```text
existing 0168 read-only Actions fetch
-> 0281-r3 sync adapter selected through --sync-tool
-> existing 0167 raw server dataset sync
-> read sibling staging directories for the same run
-> existing 0281-r2 run assembly
-> existing 0275 semantic intake
-> local idempotent run-group report
```

The adapter infers the three known artifact identities from their locked
filenames. It waits while a required member is absent. When all members declared
by the manifest are present, it delegates all correlation and digest checks to
0281-r2 and 0275.

## Operator command

```bash
PYTHONPATH=src:. python   tools/run_github_actions_artifact_fetch_once.py   --config .var/config/github_artifact_server_fetch.ini   --repository newicody/projects   --workflow-name autodoc-controlled-research.yml   --artifact-name-prefix autodoc-   --sync-tool tools/run_github_dual_artifact_server_sync_once_0281.py   --format json
```

No second fetch loop is introduced. The existing fetcher continues to own
GitHub network access, ZIP download, safety limits and raw artifact state.

## Result and advisory retention

The stable run report is written below:

```text
<dataset_root>/index/github_dual_artifact_run_groups/
  newicody__projects/<run_id>.json
```

A ready report contains the complete 0281-r2 assembly mapping. Therefore the
full Copilot advisory returned by 0275 is locally recoverable under the intake
mapping, while the SourceCandidate remains based only on the authoritative
request.

Pending reports may progress to ready as sibling artifacts arrive. Ready or
blocked reports are replay-safe and collision guarded; a different candidate
does not overwrite them silently.

## Boundaries

```text
network: existing 0168 fetcher only
raw dataset sync: existing 0167 tool
semantic correlation: existing 0281-r2 and 0275
local write: idempotent run-group JSON report only
GitHub mutation: forbidden
SQL write: forbidden
Qdrant write: forbidden
Scheduler route: forbidden
new scheduler/orchestrator/fetcher: forbidden
```

## Repository impact

```text
newicody/autodoc: modification required
newicody/projects: no modification required
projects_repository_change_required: false
```

Only the local fetch command or local service configuration must select the new
sync adapter. The deployed Actions workflow already emits the required files.
