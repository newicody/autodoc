# Product-final specialist exchange and synthesis reuse audit

## Current and target path

```text
GitHub Issue / ProjectV2
  -> authoritative request + Copilot v2 + manifest
  -> controlled Copilot board projection
  -> local fetch and correlated research work package
  -> operator gate
  -> existing Scheduler
  -> laboratory:love-studies-local
       -> specialist:love-concept-and-affect-analyst
       -> versioned message/artifact exchange
       -> specialist:love-relational-dynamics-analyst
  -> SQL-authoritative analyses
  -> E5-384/Qdrant evidence recall
  -> 0287 evidence aggregation and contradiction handling
  -> SpecialistLiaisonSynthesis
  -> FinalSynthesisPacket
  -> FinalArtifactEnvelope
  -> controlled publication on the source Issue
  -> ProjectV2 / Issue readback
```

## Canonical reuse boundaries

The existing specialist/laboratory message contract is the exchange base. It is
versioned and extended; no parallel exchange framework is introduced.

The existing liaison synthesis remains the global mutualization boundary.
Specialists normally provide deep domain analyses. Local synthesis is allowed
when requested, while global synthesis occurs after analyses have been
collected and evidence/contradictions have been evaluated.

The existing Scheduler owns visit submission and every request for another
specialist or laboratory. A specialist never invokes another specialist
directly.

## Concrete versus fake laboratory

`laboratory:local-fake` remains a deterministic test provider. The product
prototype receives a separate `autodoc_native` provider named
`laboratory:love-studies-local`; this avoids changing the public meaning of the
fake provider and preserves existing tests.

## Publication separation

The Copilot first opinion and the final specialist deliverable are two distinct
publications with distinct schemas, markers and plan digests:

```text
Copilot advisory publication = early, consultative, non-authoritative
final deliverable publication = post-analysis, post-synthesis, operator-gated
```
