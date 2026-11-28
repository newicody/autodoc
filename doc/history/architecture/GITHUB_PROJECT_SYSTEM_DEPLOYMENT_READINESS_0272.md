# GitHub Project system deployment readiness — 0272-r5

## Purpose

Test whether the existing local ProjectV2 reader, snapshot change detector and
secondary GitHub Actions artifact workflow are correctly configured and already
deployed.  The phase deliberately provides no installation or deployment
script.

## Reuse audit

- reuses `config/github_project_v2_query_only.example.ini` and the 0165 loader;
- reuses the 0272-r3 query-only document validator and Project identity;
- reuses the existing workflow and standalone builder templates;
- checks the 0272-r4 change detector instead of creating another diff surface;
- adds only a readiness-specific REST GET boundary because no existing public
  surface compares a deployed workflow and builder with their local templates.

## Checks

Local mode verifies configuration, required Python tools, template presence and
workflow safety.  Live mode additionally verifies ProjectV2 identity, active
workflow metadata, deployed workflow content and deployed builder content.
Template and deployed contents are compared by SHA-256.

## Boundaries

The CLI may perform GraphQL query POST and REST GET operations.  It never sends a
GraphQL mutation or REST write, never dispatches a workflow, never installs or
deploys files, and never writes SQL, Qdrant, SHM or Scheduler state.  The token
value is read from the configured environment variable and is never serialized.
