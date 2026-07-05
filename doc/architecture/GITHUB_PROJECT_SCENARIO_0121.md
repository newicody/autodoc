# 0121 — GitHub Project scenario contract

This phase models the baby-fork GitHub Project loop without connecting to the
GitHub API.

Required path:

```text
GitHub artifact -> SourceCandidate SQL -> ContextExplorationPlan -> LLMSpecialistResult -> GitHubProjectPublication
```

The module is `GitHubProjectScenario` in the sense of a data-only scenario
contract. It serializes the path from an external project artifact to a future
publication packet that another adapter can post back to GitHub.

## Authority boundaries

- SQLContextStore is durable context authority.
- Qdrant is vector projection and retrieval, not context authority.
- OpenVINO produces embeddings behind adapter.
- LLM is specialist producer, not context authority.
- Scheduler orchestrates context exploration jobs; it does not build variants itself.
- MVTC remains future, not runtime in 0121.

## Runtime imports

No GitHub API/HTTP/socket runtime import in GitHubProjectScenario. The module
also avoids Qdrant/OpenVINO/PostgreSQL/LLM runtime imports. The future live
GitHub client must sit behind a separate adapter and feed these contracts with
already-fetched artifacts.

## Local pipeline intent

```text
external GitHub adapter later
-> GitHubProjectArtifact
-> GitHubSourceCandidate(sql_record kind github_artifact)
-> SQLContextStore upsert by caller
-> ContextExplorationPlan
-> SQL hydration / embeddings / Qdrant projection / LLM specialist
-> GitHubProjectPublication
-> external GitHub adapter later
```

The GitHub publication packet contains references and bounded candidate
summaries. It does not embed heavy payloads or make network calls.
