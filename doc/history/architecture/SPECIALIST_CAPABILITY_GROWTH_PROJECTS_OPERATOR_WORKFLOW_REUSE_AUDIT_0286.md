# Specialist capability growth Projects operator workflow reuse audit — 0286-r1

## Decision

GitHub Projects reste non autoritatif. It exposes requests, approved local decisions, revision status and readback evidence, but cannot approve a capability, write the SQL history or select a specialist revision.

The implementation must reuse:

- `src/context/github_controlled_advisory_issue_publication_0281.py` for idempotent digest-bound Issue comments;
- `tools/apply_github_project_v2_operator_authorized_mutations_0282.py` for preview-first, explicitly authorized ProjectV2 mutations through the established `gh` boundary;
- the append-only ProjectV2 cycle/history contracts from 0282;
- the complete 0285 specialist capability-growth chain.

## Authority boundaries

- Scheduler reste l’unique autorité d’orchestration.
- SQL reste l’autorité durable.
- Qdrant reste projection/rappel and never validates a revision.
- EventBus, PassiveSupervisor and Cell Lens remain observational.
- Copilot remains optional and advisory.
- A GitHub Issue or ProjectV2 field is a workflow/read projection, not a specialist descriptor or durable decision record.

## Current bundle gap

The current `projectv2_views.json` describes generic theme, display, server and Copilot fields. It does not yet expose `specialist_ref`, revision identity, capability action, operator decision, durable `sql_ref` or a dedicated specialist-revision review view. Existing research/update/theme forms remain useful but should not be overloaded with a domain-specific approval protocol.

## Required controlled path

```text
GitHub request form
→ normalized non-authoritative request
→ local 0285 proposal/revision/operator gate
→ SQL-authoritative history
→ Scheduler-approved selection
→ immutable Projects review projection
→ preview publication plan
→ explicit operator confirmation + exact digest
→ existing Issue/ProjectV2 adapters
→ query-only readback
→ correlated closure proof
```

No new HTTP client, Scheduler, global registry or laboratory manager is allowed.
