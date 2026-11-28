# Architecture — 0287-r7-r13 final deliverable publication plan

## Position in the chain

```text
Scheduler-managed r11 collaboration
              ↓
r12 SQL/E5/Qdrant/evidence/liaison closure
              ↓
FinalArtifactEnvelope
              ↓
r13 pure publication plan
       ┌──────┴────────┐
       ↓               ↓
source Issue       ProjectV2 item
comment plan       field plan
       └──────┬────────┘
              ↓
       one plan_digest
              ↓
 exact dual-surface readback expectation
```

## Human rendering

The source Issue receives a final deliverable, not another first-pass Copilot
advisory. The marker namespaces therefore remain distinct:

```text
autodoc:copilot-advisory:...     initial advisory

autodoc:copilot-advisory-v2:... refined advisory

autodoc:final-deliverable:...    final laboratory deliverable
```

The final comment renders the r12 envelope body and explicitly preserves
convergences, contradictions, uncertainties, recommendations and folded
provenance references.

## ProjectV2 snapshot reuse decision

The existing 0286 live readback tool exposes ProjectV2 fields as sorted
`(name, value)` tuples bound to the capability-growth workflow. There is no
generic immutable snapshot carrying the item id, field node ref, field name and
value together. r13 therefore introduces only that minimal read-only value
object; it does not create a new readback adapter or GraphQL client.

## Planning semantics

### Source Issue

- no matching marker: `create`;
- one exact matching comment: `replay`;
- one changed matching comment or several matches: `collision`.

### ProjectV2

- no supplied field snapshot: `update`;
- exact item/field/value snapshot: `replay`;
- same item and field with another value: `update`;
- another item or field identity: `blocked`.

### Combined action

| Issue | ProjectV2 | Combined action |
|---|---|---|
| create | update | `create_and_project` |
| create | replay | `create_issue` |
| replay | update | `project` |
| replay | replay | `replay` |

A collision or blocked identity emits no operation.

## Digest boundary

The plan digest covers:

- repository, Issue number and source Issue reference;
- final-deliverable marker;
- exact Issue body SHA-256;
- exact ProjectV2 projection including its value SHA-256;
- policy decision identity and operator decision.

A later executor must require the operator-confirmed digest before mutation.
Changing the policy, final document or ProjectV2 value therefore creates a new
plan digest.

## Readback boundary

The verifier is pure and expects:

- exactly one Issue comment carrying the marker;
- exact equality with the approved body;
- the exact ProjectV2 item and field identities;
- exact equality with the approved field value.

It performs no repair and no remote mutation. Recovery belongs to the later
closed-loop recovery phase.

## Ownership

| Surface | r13 role |
|---|---|
| Scheduler | unchanged; no publication orchestration added |
| r12 final envelope | authoritative synthesis input |
| SQL | unchanged |
| E5/OpenVINO | unchanged |
| Qdrant | unchanged |
| GitHub Issue | planned, not mutated |
| ProjectV2 | planned, not mutated |
| Operator gate | approval already required; exact digest prepared |
| Readback | exact expectation and pure verification |
