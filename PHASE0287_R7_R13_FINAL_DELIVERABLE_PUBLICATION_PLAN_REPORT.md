# Phase 0287-r7-r13 — Final deliverable publication plan

## Objective

Close the planning boundary immediately after the r12 `FinalArtifactEnvelope`:

```text
r12 final artifact envelope
→ deterministic human-readable Markdown
→ distinct final-deliverable marker
→ Issue create/replay/collision decision
→ concise ProjectV2 field update/replay decision
→ exact combined plan digest
→ exact Issue + ProjectV2 readback expectation
```

This phase prepares publication. It does not execute a network mutation.

## Reuse audit

The phase reuses existing repository surfaces instead of creating a publication
manager or another orchestration layer:

- `GitHubIssueCommentSnapshot` from
  `github_controlled_advisory_issue_publication_0281.py`;
- the established create/replay/collision semantics of controlled Issue
  publication planners;
- the established pure ProjectV2 mutation-plan and readback boundaries;
- the 0286 query-only readback tools, whose field snapshots are currently
  capability-growth-specific mapping tuples rather than a reusable generic
  immutable contract; r13 therefore adds only the minimal generic single-field
  snapshot required by the final publication plan;
- the r12 `LoveMemoryEvidenceSynthesisResult` and `FinalArtifactEnvelope` as the
  only final synthesis input;
- the existing operator decision and exact `plan_digest` execution pattern.

No new CLI, GitHub client, GraphQL client, Scheduler, queue, manager, registry,
SQL store, Qdrant client or inference runtime is introduced.

## Result

`love_final_deliverable_publication_plan_0287.py` provides:

- a deterministic bounded Markdown renderer;
- the marker namespace `autodoc:final-deliverable:<digest>`, separate from all
  Copilot advisory comments;
- typed immutable Issue and ProjectV2 planning data;
- collision-safe Issue comment planning;
- deterministic ProjectV2 update/replay planning against a supplied snapshot;
- a combined SHA-256 `plan_digest` covering the Issue body, ProjectV2 projection,
  source identity and policy decision;
- exact readback verification for both publication surfaces.

The human document retains:

- the final synthesis body;
- convergences;
- contradictions;
- uncertainty and unresolved points;
- recommendations;
- evidence, context influence and validation references in a folded provenance
  section.

## Authority boundaries

- Scheduler modified: no.
- ControlProxy modified: no.
- SQL modified: no.
- Qdrant modified: no.
- OpenVINO modified: no.
- GitHub mutation performed: no.
- ProjectV2 mutation performed: no.
- Operator approval required: yes.
- Exact confirmed plan digest required by the future executor: yes.
- Exact remote readback required after future execution: yes.

## Code-rule review

- standard library only for the new contract;
- immutable typed `dataclass(frozen=True, slots=True)` command, plan, operation,
  projection and readback structures;
- composition of existing publication snapshots and planning semantics;
- no business logic in a CLI because no CLI is added;
- deterministic JSON canonicalization and SHA-256 identities;
- no direct backend, network, Scheduler or laboratory call.

## Live-path status

The r13 contract is executable and tested but intentionally not wired to a
remote adapter. It is the approved pure boundary that r14 will exercise in one
correlated local smoke. Real GitHub/ProjectV2 mutation remains deferred to r15.

## Failure modes

Planning fails closed when:

- the input is not the closed r12 result;
- liaison synthesis is not publication-ready;
- the study result is not synthesized;
- r12 already reports a GitHub mutation;
- final envelope identity or body is missing;
- several Issue comments carry the same final marker;
- a marked Issue comment has different content;
- the supplied ProjectV2 snapshot addresses another item or field.

Readback fails closed when the exact Issue body or exact ProjectV2 value cannot
be observed after a future mutation.

## Verification

The patch includes functional tests for:

- deterministic planning;
- combined Issue and ProjectV2 operations;
- exact replay;
- Issue collision;
- ProjectV2 identity mismatch;
- digest sensitivity to policy and projected value;
- exact readback confirmation and mismatch rejection;
- incomplete or already-mutated r12 input rejection.

Rule tests verify reuse, marker separation, pure planning, absent parallel
runtime classes, exact readback requirements and complete documentation.

## Next phase

`0287-r7-r14` should consume this plan in a deterministic closed-loop smoke:
validate the exact digest, simulate the already-existing Issue/ProjectV2 adapter
boundaries, then verify both readbacks. It must still avoid a real network
mutation.
