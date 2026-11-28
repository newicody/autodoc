# Operational plan 0123 — local review before external publication

Status: transition boundary.

The context path now reaches a local review packet:

```text
SQLContextStore -> SQLContextHydrator -> OpenVINOEmbeddingAdapter -> QdrantProjectionAdapter -> LLMSpecialistAdapter -> GitHubProjectScenarioPacket -> ContextGraphSnapshot -> GitHubPublicationReviewPacket
```

Rules preserved:

- SQLContextStore is durable context authority.
- Qdrant is vector projection and retrieval, not context authority.
- OpenVINO produces embeddings behind adapter.
- LLM is specialist producer, not context authority.
- GitHub publication review is local and reviewable; it does not post to GitHub.
- Scheduler orchestrates context exploration jobs; it does not publish reviews itself.
- MVTC remains future, not runtime in 0123.

Next likely step: add an explicit dry-run external publication command contract, still without live GitHub API calls.
