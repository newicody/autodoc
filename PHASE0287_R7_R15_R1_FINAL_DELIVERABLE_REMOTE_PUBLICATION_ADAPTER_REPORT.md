# Phase 0287-r7-r15-r1 — Final deliverable remote publication adapter

## Objective

Add the smallest controlled remote boundary required after the deterministic
r13 plan and r14 local smoke:

```text
r13 immutable publication plan
→ current Issue and ProjectV2 read preflight
→ create/update/replay/collision decision
→ explicit operator approval
→ three remote mutation locks
→ exact plan_digest confirmation
→ Issue comment mutation when required
→ ProjectV2 field mutation when required
→ exact remote readback through the r13 verifier
```

This unit does not claim live closed-loop evidence. It prepares and tests the
controlled adapter needed by the subsequent real-run units of r15.

## Reuse audit

The implementation reuses:

- `love_final_deliverable_publication_plan_0287.py` as the immutable source of
  the approved body, ProjectV2 value, operation identities and `plan_digest`;
- `GitHubIssueCommentSnapshot` from the controlled advisory publication
  contract rather than introducing another Issue snapshot model;
- `verify_love_final_deliverable_publication_readback()` for the exact final
  Issue plus ProjectV2 verification;
- the existing `gh api` REST and GraphQL boundary pattern under `tools`.

No synthesis, Scheduler, SQL, Qdrant, OpenVINO, laboratory or specialist logic
is duplicated in the adapter.

## Added domain boundary

`love_final_deliverable_remote_publication_0287.py` contains:

- immutable command and result dataclasses;
- typed Issue and ProjectV2 publication protocols;
- JSON rehydration of the exact r13 plan, including an r14 result carrying the
  plan under `publication_plan`;
- preflight create/update/replay/collision decisions;
- execution lock and digest validation;
- ordered Issue then ProjectV2 mutation;
- explicit partial-execution reporting;
- final exact readback delegated to r13.

The domain module has no network, environment, subprocess or CLI dependency.

## Added local adapter

`tools/publish_love_final_deliverable_0287.py` is preview-only by default. It
uses GitHub CLI for:

- paginated Issue comment reads;
- Issue comment creation;
- ProjectV2 item, field and current-value GraphQL reads;
- `updateProjectV2ItemFieldValue` for text, single-select, date or number
  fields;
- post-mutation remote readback.

Execution requires all of the following:

```text
--operator-decision approve
--execute
--confirm-plan-digest <exact r13 digest>
AUTODOC_REMOTE_MUTATION_ALLOWED=true
AUTODOC_ISSUE_PUBLICATION_ALLOWED=true
AUTODOC_PROJECT_PROJECTION_ALLOWED=true
```

The token is read from `AUTODOC_PROJECT_TOKEN` by default and exposed to
GitHub CLI as `GH_TOKEN` only in the child process environment.

## Idempotence and collision behavior

Issue surface:

- no exact marker: `create`;
- one marker with exact body: `replay`;
- one marker with another body: `collision`;
- multiple matching markers: `collision`.

ProjectV2 surface:

- missing or different value with exact item/field identity: `update`;
- exact value: `replay`;
- item, field id or field name mismatch: `collision`.

After execution, success is reported only when the r13 verifier confirms both
surfaces exactly.

## Partial execution

The Issue operation precedes the ProjectV2 operation, matching the r13
operation dependency. If Issue creation succeeds and ProjectV2 mutation fails,
the result is invalid, marked `partial`, retains the created comment identity
and exposes the transport error. A later run can then observe the exact Issue
comment as replay and retry only the ProjectV2 projection.

## Authority boundaries

- Scheduler: not used and not modified.
- Laboratory and specialists: not used and not modified.
- SQL: not used and not modified.
- Qdrant: not used and not modified.
- OpenVINO/E5: not used and not modified.
- GitHub mutation: possible only in the tool adapter after all explicit gates.
- ProjectV2 mutation: possible only in the same controlled execution.
- r13 plan: immutable and never recalculated by this phase.

## Code-rule review

- existing publication planners, snapshots and readback verifier were audited
  and reused;
- no manager, Scheduler, orchestrator, queue, registry or parallel authority was
  added;
- the domain command/result are frozen typed dataclasses;
- environment and CLI parsing remain under `tools`;
- remote mutation is closed by default;
- the exact approved digest is required at the mutation boundary;
- failures and partial execution remain explicit rather than being hidden;
- no dependency, generated SVG or binary patch hunk is added.

## Tests

Functional domain tests cover:

- preview without mutation;
- successful Issue plus ProjectV2 execution and exact readback;
- fully idempotent replay;
- digest mismatch before mutation;
- Issue marker collision;
- partial execution after ProjectV2 failure;
- ProjectV2 identity collision;
- direct r13 and nested r14 plan parsing.

Tool tests cover paginated Issue reads, comment creation, ProjectV2 field
metadata resolution and the exact GraphQL text mutation payload.

Rule tests cover bundle completeness, r13 reuse, separation of domain and
transport, the three locks, absence of local authority changes, source-only DOT
and the remaining r15 roadmap.

## Live-path status

The adapter is ready for a controlled real invocation but this patch does not
perform one. Therefore `0287-r7-r15` remains open and no live evidence claim is
made.

## Remaining r15 plan

### `0287-r7-r15-r2 — imported Actions run to approved publication execution`

Consume one actually fetched three-artifact Actions run, execute the existing
r14 composition through the local authorities, extract its exact r13 plan and
feed that plan to this adapter. The unit must retain workflow run id, artifact
ids, source Issue identity, operator decision and the same `plan_digest` in one
correlated execution result.

### `0287-r7-r15-r3 — live Issue and ProjectV2 closed-loop evidence`

Run the controlled command against `newicody/projects`, record the real Actions
run and artifact identities, exact Issue comment URL, ProjectV2 readback,
replay result and negative gate checks. Only this evidence unit may close r15.

`0287-r7-r16` remains the recovery, installation and prototype-closure phase.
