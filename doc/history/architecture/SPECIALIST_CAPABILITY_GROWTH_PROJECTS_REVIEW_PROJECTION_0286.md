# Specialist capability-growth Projects review projection — 0286-r2

## Purpose

Expose the result of the local 0285 capability-growth loop as one stable review
projection that later GitHub adapters can preview and publish.  The projection
is a contract, not a GitHub client and not a publication command.

## Input boundary

The builder consumes the structural mapping exposed by the 0285 closed-loop
smoke result.  It requires all of the following evidence to be true:

- the 0285 loop is closed without unresolved issues;
- the operator gate approved the candidate revision;
- SQL-authoritative durable history was recorded;
- the existing Scheduler selected the approved revision;
- the existing laboratory path completed;
- the EventBus observation was published;
- the PassiveSupervisor read model is valid;
- neither GitHub mutation nor Qdrant authority is claimed.

## Correlation

The projection rejects drift between:

- proposal, revision and decision references/digests;
- history entry, SQL reference and Scheduler selection;
- selected revision and approved candidate revision;
- EventBus observation, passive read model and selection;
- capability, conversation and context references.

## ProjectV2 preview values

The contract prepares deterministic values for the future fields:

- `Spécialiste`;
- `Révision spécialiste`;
- `Capacité proposée`;
- `Action capacité`;
- `Décision capacité`;
- `Statut révision`;
- `Référence SQL`;
- `Digest décision`;
- `Laboratoire`.

These values are preview data only.  The phase does not create fields, publish a
comment or mutate a ProjectV2 item.

## Authority boundaries

```text
0285 closed-loop evidence
        |
        v
immutable 0286-r2 review projection
        |
        +--> future publication plan (0286-r5)
        +--> future operator-authorized adapter (0286-r6)

SQL       = durable authority
Scheduler = orchestration authority
GitHub    = review/workflow surface
Qdrant    = projection and recall only
EventBus  = observation only
Copilot   = advisory only
```

No new Scheduler, global specialist registry, HTTP client, EventBus,
PassiveSupervisor or LaboratoryManager is introduced.

## Installation

`templates/github/projects-repository/INSTALLATION.md` was reviewed.  No update
is required because 0286-r2 does not change the deployable Projects bundle.  The
next required cumulative installation update is 0286-r3, together with the new
Issue form.
