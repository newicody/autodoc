# Specialist capability-growth Projects publication plan — 0286-r5

## Purpose

Convert the closed local capability-growth review projection into one stable
publication intent before any remote mutation is possible.

The plan has two coordinated parts:

1. an append-only Issue comment with an invisible idempotency marker;
2. the nine ProjectV2 field values already declared by 0286-r4.

Both parts are covered by a single `plan_digest`.

## Comment state machine

```text
no matching marker       -> create
one identical comment    -> replay
one different comment    -> collision
multiple matching marker -> collision
```

A collision blocks ProjectV2 writes too.  This prevents a card from appearing
consistent while its append-only review comment has diverged.

## Field state machine

For every allowed field:

```text
current != desired -> set
current == desired -> replay
```

Only these fields are accepted:

- `Spécialiste`;
- `Révision spécialiste`;
- `Capacité proposée`;
- `Action capacité`;
- `Décision capacité`;
- `Statut révision`;
- `Référence SQL`;
- `Digest décision`;
- `Laboratoire`.

The plan cannot write `Résumé`, `Serveur`, Copilot fields or any arbitrary
ProjectV2 field.

## Digest boundary

The digest covers:

- repository, Issue and ProjectV2 item identity;
- local policy decision identity;
- review, revision and SQL references;
- r2 projection digest;
- comment marker and body digest;
- every current/desired field value and action;
- the combined publication action.

Any changed value requires a newly reviewed digest.

## Authority

```text
0285 SQL-authoritative closed loop
        |
        v
0286-r2 immutable review projection
        |
        v
0286-r5 publication plan (no mutation)
        |
        v
0286-r6 existing operator-authorized GitHub boundary

SQL       = durable authority
Scheduler = orchestration authority
GitHub    = review/workflow surface
Qdrant    = projection and recall only
Copilot   = advisory only
```

## Installation

`templates/github/projects-repository/INSTALLATION.md` was reviewed.  No update
is required because r5 adds no deployable Projects file.  The guide remains at
`0286-r4`; it will change only when a workflow, form, field/view, variable,
permission or deployed adapter procedure changes.

## Code-rule alignment

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: pure typed plan, policies explicit, IO deferred to an adapter
live_path_status: n/a
live_path_uses_real_backend: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```

Next: `0286-r6-specialist-capability-growth-projects-operator-authorized-adapter`.
