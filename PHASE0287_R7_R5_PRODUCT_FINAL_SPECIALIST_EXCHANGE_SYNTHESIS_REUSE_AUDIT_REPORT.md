# Phase 0287-r7-r5 — product-final specialist exchange and synthesis reuse audit

## Objective

Audit the current master after 0287-r7-r4, compare the implemented chain with
the requested final product, lock reuse decisions, and replace the active
walking-skeleton order with a product-final roadmap. This phase is documentation
and executable architecture evidence only.

baseline_commit: 9128bbb
code_rule_review: done
code_rule_update_required: false
live_path_status: audit

## Product objective

```text
source Issue / ProjectV2 item
-> authoritative context artifact + Copilot advisory artifact
-> advisory visible on the board
-> artifacts fetched by Autodoc
-> correlated work package delivered to specialists
-> concrete laboratory executing two real domain specialists
-> deep analyses retained with evidence and provenance
-> later liaison synthesis
-> final human deliverable
-> controlled publication on the source Issue
-> ProjectV2 / Issue readback and idempotent replay
```

The initial concrete domain is love studies. The specialists are simple and
deterministic, but they perform real analysis rather than returning a prepared
fake scenario.

## Deep code audit

### GitHub ingress and Copilot

Implemented:

- Actions produces authoritative request, Copilot advisory and correlation
  manifest artifacts;
- the active producer emits `missipy.github.copilot_advisory.v2`;
- local contracts and intake read v1 and v2;
- the operator/laboratory projection exposes the four v2 analytical fields.

Missing:

- the deployed Projects publication builder remains v1-oriented;
- controlled Issue publication renders v1 summary/route/confidence fields;
- no complete proof publishes v2 to the board and reads it back.

### Artifact fetch and research context

Fetch, run assembly, strict digest correlation and SourceCandidate intake exist.
They do not yet form one canonical research work package delivered to a
concrete laboratory. The source request remains authoritative and the advisory
remains hint-only; this boundary is correct and retained.

### Laboratory runtime

The Scheduler-owned laboratory protocol, descriptor, visit request/result,
resource budget and runtime-registry binding plan exist. The only active
provider is the deterministic fake provider. Its output explicitly declares
`provider_kind=local_fake` and `real_backend_used=false`. The GitHub laboratory
wrapper is statically typed to the fake closed-loop smoke command.

Decision: add a distinct `autodoc_native` provider later. Do not mutate or
rename the fake provider into a real one.

### Portable specialists and exchanges

Portable specialist descriptors, capabilities, execution profiles, laboratory
bindings and transfer continuity already exist.

`specialist_laboratory_message_contract_0284.py` already standardizes:

- `message_ref`, `conversation_ref` and `visit_ref`;
- contiguous `sequence_no` ordering;
- demand/opinion/context/specialist/laboratory/result/acknowledgement kinds;
- sender, recipient, origin and target laboratory;
- contract and return-route references;
- immutable payload, context, evidence and observation references;
- `reply_to_message_ref` and ordered conversation validation.

This is the canonical exchange foundation. It is not yet sufficient for the
product-final path because it lacks first-class artifact digest/idempotency
identity, explicit completion/error semantics and clean cross-visit analysis
continuation. Those changes require an explicit v2 contract, not a second
parallel exchange abstraction.

### Analysis and synthesis

`server_oriented_deliberation_cycle.py` already defines orientation,
preliminary specialist opinions, refined demands, rounds, passive statistics
and `FinalArtifactEnvelope`.

`specialist_liaison_synthesis.py` already defines specialist path traces,
`SpecialistOutputFragment`, `SpecialistLiaisonSynthesis`, end-user sections and
`FinalSynthesisPacket`.

The current fake-laboratory composition proves these pieces can be assembled,
but it adapts fake visit results and is not fed by real domain specialists.
The liaison layer is also historically coupled to `LLMSpecialistResult` in some
builders. It must be extended with a generic domain-analysis adapter rather than
replaced.

Locked semantic rule:

- specialists primarily produce deep analyses in their domain;
- they may produce a local synthesis when explicitly requested;
- the mutualized/global synthesis normally happens later through the liaison
  stage after multiple analyses are available.

### Memory and multi-laboratory evidence

The real-memory closure already proves SQL authority, OpenVINO multilingual E5
384-dimensional passage/query embeddings, Qdrant reference-only projection and
SQL rehydration. The 0287 chain already provides evidence aggregation,
provenance, digest deduplication, contradiction detection, operator weighting
and durable history.

These are implemented as separate closures. They are not connected to the
GitHub research package, a concrete laboratory, real specialist analyses or the
final liaison synthesis.

### Final publication

The repository has controlled advisory Issue publication with deterministic
Markdown, markers, collision detection, plan digest and replay behavior. It
publishes the Copilot advisory, not a specialist deliverable, and it validates
the v1 preview schema.

`FinalArtifactEnvelope` exists but has no dedicated controlled source-Issue
publication planner/readback path. The final deliverable publication must use a
separate marker and schema from the initial Copilot advisory publication.

## Reuse matrix

| Product need | Existing canonical surface | Decision |
|---|---|---|
| specialist exchange | `specialist_laboratory_message_contract_0284.py` | version/extend |
| cross-laboratory continuity | `specialist_laboratory_transfer_contract_0284.py` | reuse |
| specialist orchestration | existing Scheduler visit binding | reuse |
| concrete lab | fake provider is explicitly fake | add native provider |
| deep analysis output | output fragments plus new generic analysis contract | extend |
| global synthesis | liaison synthesis and final packet | reuse/extend |
| semantic recall | SQL + E5-384 + Qdrant closure | reuse/connect |
| contradictions and weighting | 0287 evidence chain | reuse/connect |
| Copilot publication | existing controlled planners | add v2 branch |
| final deliverable publication | controlled publication patterns | add distinct planner |
| observation | EventBus / PassiveSupervisor / VisPy | reuse |

## Prototype specialists

- `specialist:love-concept-and-affect-analyst` performs deep analysis of
  concepts, affective dimensions, textual evidence, uncertainty and missing
  information.
- `specialist:love-relational-dynamics-analyst` performs deep analysis of
  reciprocity, communication, expectations, boundaries, asymmetries and
  relational dynamics.

Neither specialist is the permanent global synthesizer. Their analyses are
mutualized later by the liaison stage.

## Documentation and deployment review

`templates/github/projects-repository/INSTALLATION.md` was reviewed. This audit
does not change workflows, services, secrets or deployment commands, so the
cumulative installation guide is intentionally unchanged.

## Closure

This phase closes the reuse audit and roadmap adaptation only. It performs no
runtime registration, specialist execution, SQL/Qdrant write, OpenVINO call,
GitHub mutation or ProjectV2 mutation.
