# ControlProxy operational plan — 0123-r2

0123-r2 corrects the 0123 direction. The next operational layer is not a GitHub publication review. It is a local liaison/synthesis layer that unifies specialist outputs before any final publication.

## Orientation

```text
InferenceContextDraft
-> Specialist outputs
-> SpecialistOutputFragment[]
-> SpecialistLiaisonSynthesis
-> FinalSynthesisPacket only after liaison
-> later external adapter
```

SpecialistLiaisonSynthesis unifies specialist work before any final publication.

Specialist path observations are bus-ready facts, not commands.

VisPy can represent specialist paths from bus observations later.

No GitHub/DOT publication review in 0123-r2.

## Authority boundaries

- SQLContextStore is durable context authority.
- Qdrant is vector projection and retrieval, not context authority.
- OpenVINO produces embeddings behind adapter.
- LLM is specialist producer, not context authority.
- Scheduler orchestrates jobs; it does not perform specialist liaison synthesis itself.
- The bus can observe specialist paths; it does not command specialist execution.

## Next after 0123-r2

The next real step should be either:

1. a local integration runner that composes SQL hydration, embedding, retrieval, specialist output, and liaison synthesis in a single importable function; or
2. a VisPy/event viewer that consumes observation facts without becoming an authority.
