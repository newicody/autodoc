# GitHub Actions ready-run Copilot Issue publication — 0287 r16-r4-r2

## Goal

Make the Copilot first opinion visible below every GitHub Issue whose inference
workflow produced one valid correlated three-artifact run.

The GitHub Actions workflow remains an artifact producer with `issues: read`.
Remote publication is performed only by the local Autodoc connector after the
artifacts have been fetched and validated.

## Existing surfaces reused

- `tools/run_github_actions_artifact_scan_once_live_0272.py` fetches and
  correlates the three artifacts into `ready_runs`.
- `templates/github/projects-repository/scripts/build_copilot_advisory_v2_publication_preview.py`
  verifies request/advisory/manifest correlation and renders the v2 preview.
- `tools/publish_github_copilot_advisory_v2_issue_comment_0287.py` plans,
  publishes, detects replay/collision, and verifies GitHub readback.

The r16-r4-r2 tool composes these existing surfaces.  It does not add a second
artifact downloader or a second publication adapter.

## Data path

```text
ProjectV2 item qualified for inference
    -> local En-cours dispatcher
    -> read-only Projects workflow
    -> authoritative_request.json
    -> copilot_advisory.json
    -> dual_artifact_manifest.json
    -> local fetch and ready_run
    -> durable raw dataset resolution
    -> v2 preview validation
    -> local publication plan
    -> explicit local policy and operator approval
    -> GitHub Issue comment
    -> GitHub comment readback
    -> local completion receipt
```

## Automatic one-shot contract

`run_github_actions_ready_run_copilot_issue_publication_once_0287.py` accepts a
scan report and processes the newest uncompleted `ready_runs`, bounded by
`--max-runs`.  `--run-id` may narrow a first live test.

Preview mode reads GitHub comments through the existing publisher but performs
no mutation and writes no completion receipt.

Execute mode additionally requires:

- `--policy-decision-id policy:...`;
- `--operator-decision approve`;
- `AUTODOC_REMOTE_MUTATION_ALLOWED=true`;
- `AUTODOC_ISSUE_PUBLICATION_ALLOWED=true`.

The wrapper obtains the deterministic plan, carries its digest into the execute
call, and records completion only when the existing publisher reports verified
readback.  `created` and `replay-noop` are both successful idempotent outcomes.

## Durable address

A ready-run artifact is resolved from:

```text
<dataset-root>/raw/<owner>__<repository>/<run-id>/<artifact-id>/<member-name>
```

Expected members are exactly:

- `authoritative_request.json`;
- `copilot_advisory.json`;
- `dual_artifact_manifest.json`.

Staging directories are not an execution authority.

## Boundaries

- GitHub Actions retains `issues: read`.
- No `gh run download` is performed by this unit.
- No ProjectV2 field mutation is performed yet.
- No SQL or Qdrant write occurs.
- Scheduler and laboratory execution do not start.
- The Issue body remains the authoritative request.
- The Copilot comment remains advisory and non-authoritative.
