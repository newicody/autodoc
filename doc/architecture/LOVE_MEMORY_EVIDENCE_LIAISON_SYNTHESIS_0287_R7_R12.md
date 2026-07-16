# Architecture — 0287-r7-r12

## Data path

```text
NativeLoveCollaborationRecord
  ├─ concept/affect analysis
  └─ relational-dynamics analysis
        ↓
SQL authority objects + artifact descriptors
        ↓
injected projection port
  OpenVINO/E5 384 → Qdrant dense_e5_v1
        ↓
hybrid dense+sparse query under revision/branch/security filters
        ↓
Qdrant returns references only
        ↓
SQL membership and digest verification
        ↓
SQL-authoritative rehydration
        ↓
local evidence mutualization
        ↓
SpecialistLiaisonSynthesis
        ↓
FinalSynthesisPacket
        ↓
FinalArtifactEnvelope
```

## Authority boundaries

| Surface | Role |
|---|---|
| SQL | Durable objects, artifacts, revisions, relations and projection metadata |
| OpenVINO/E5 | Existing injected query/passage embedding runtime |
| Qdrant | Reconstructible projection and reference selection |
| Scheduler | Already completed the two r11 visits; unchanged in r12 |
| ControlProxy | No role in semantic persistence or synthesis |
| GitHub | No mutation; publication is deferred to r13 |

## Local versus multi-laboratory evidence

The current contribution set contains two specialists but one laboratory. The
liaison step may compare and synthesize their work, but it may not claim the
stronger multi-laboratory provenance contract. The 0287 multi-laboratory
aggregation, digest deduplication, contradiction policy and durable history are
only eligible when at least two distinct `laboratory_ref` values exist.

## Context revisions

The first accepted child revision adds the two analyses and their artifacts. A
second accepted child revision adds the liaison synthesis and final artifact.
Past revisions remain immutable and reproducible.
