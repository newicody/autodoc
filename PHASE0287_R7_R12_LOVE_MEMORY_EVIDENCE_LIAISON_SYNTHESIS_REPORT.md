# Phase 0287-r7-r12 — Love memory, evidence and liaison synthesis

## Objective

Close the local post-specialist chain without inventing new authority or orchestration:

```text
r11 two Scheduler visits
→ two real specialist analyses
→ SQL authority
→ injected OpenVINO/E5 projection
→ Qdrant reference-only recall
→ SQL rehydration
→ local evidence mutualization
→ SpecialistLiaisonSynthesis
→ FinalSynthesisPacket
→ FinalArtifactEnvelope
```

## Reuse audit

The phase reuses the following existing surfaces:

- `SQLiteContextRevisionAuthorityStore` for durable objects, revisions, relations,
  artifacts and projection metadata;
- `execute_hybrid_retrieval()` for dense+sparse selection and SQL readback;
- `SpecialistOutputFragment`, `SpecialistLiaisonSynthesis` and
  `FinalSynthesisPacket` for human synthesis;
- `FinalArtifactEnvelope` as the final local handoff boundary;
- the existing r11 `NativeLoveCollaborationRecord` as the two-specialist input.

No OpenVINO runtime, Qdrant client, Scheduler, EventBus, ControlProxy or GitHub
adapter is created by this phase.

## Authority and storage result

The two specialist analyses are stored as digest-addressed SQL authority objects.
Their exchanged artifacts remain independent artifact descriptors. Each analysis
is projected through an injected port that must prove normalized E5 embeddings
with dimension 384 and an active `dense_e5_v1` Qdrant projection. SQL stores only
projection metadata, never vector values.

The hybrid recall must return both analysis references and rehydrate their exact
content from SQL. A missing analysis, inactive membership or digest mismatch
fails closed.

## Evidence and synthesis result

The two specialist contributions are compared locally for convergences,
contradictions, uncertainties and recommendations. They are then normalized into
three fragments: one per specialist and one local mutualization fragment. The
existing liaison builder produces a publication-ready final packet and envelope.

Both specialists currently execute inside `laboratory:love-studies-local`.
Therefore:

```text
distinct specialists = 2
distinct laboratories = 1
multi-laboratory pipeline eligible = false
multi-laboratory aggregation performed = false
```

The existing 0287 multi-laboratory evidence pipeline is deliberately deferred
until a second distinct laboratory contributes. The phase does not mislabel two
specialists in one laboratory as multi-laboratory validation.

## Closed boundaries

- Scheduler modified: no.
- ControlProxy modified: no.
- GitHub mutation: no.
- New inference backend: no.
- New Qdrant client: no.
- Global publication: no; r13 owns publication planning.
- `INSTALLATION.md`: reviewed and unchanged because no deployment surface changes.

## Verification

- r12 functional tests cover complete closure, SQL replay, digest failure,
  incomplete recall, single-laboratory semantics and authority boundaries;
- r11 regression tests remain green;
- rule tests verify reuse and absence of parallel runtime/backend creation.
