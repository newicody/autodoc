# Specialist capability-growth Projects request form contract — 0286-r3

## Purpose

Add a precise request surface to `newicody/projects` without turning GitHub into
an approval or execution authority. The generic research form remains available
for research work; this form is dedicated to changing one capability of one
stable specialist identity.

## Request versus proposal

The GitHub Issue is allowed to be incomplete. It may describe evidence that must
still be produced and may omit formal contract references. The local intake
therefore exposes `missing_proposal_prerequisites` and `proposal_ready` instead
of fabricating evidence or silently constructing an approved proposal.

```text
GitHub capability-growth Issue
        |
        v
existing authoritative_request artifact
        |
        v
GitHubSpecialistCapabilityGrowthIssueRequest
        |
        +--> evidence acquisition / clarification
        +--> future 0285-r2 proposal construction

operator decision remains local
SQL remains durable authority
Scheduler remains the only orchestrator
```

## Form fields

- stable `specialist_ref` and base version;
- requested action: add, refine, deprecate or restore;
- lowercase capability token;
- expected behavior and limitations;
- preliminary typed evidence references;
- evidence to produce and acceptance criteria;
- optional input/output contract references;
- optional laboratory capability requirements;
- conversation and context references;
- optional Copilot advisory request;
- mandatory acknowledgement that the Issue is not an approval.

## Local normalization

The stdlib-only contract consumes any of these existing shapes:

1. `missipy.github.authoritative_request.v1`;
2. a GitHub event containing `issue`, `repository` and `sender`;
3. a raw Issue mapping with explicit repository and actor arguments.

It parses the stable `### Label` sections produced by GitHub Issue forms,
validates typed references and emits deterministic request and revision digests.
No HTTP call, GitHub mutation, SQL/Qdrant write, Scheduler dispatch, laboratory
execution or EventBus publication occurs.

## Installation boundary

The new form is copied into `newicody/projects` by the existing rsync procedure.
No workflow permission, variable, secret or Action changes. The cumulative guide
is advanced to `0286-r3`; dry-run comparison remains mandatory and `--delete`
remains forbidden.

## Next step

`0286-r4-specialist-capability-growth-projectv2-fields-views` adds the restricted
review fields and a dedicated view. It must not make the ProjectV2 card the
source of the operator decision.

```text
projects_bundle_modified: true
projects_installation_modified: true
workflow_modified: false
scheduler_modified: false
sql_modified: false
qdrant_modified: false
external_dependencies_added: false
```
