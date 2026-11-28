# 0123 — GitHub publication review packet

GitHub publication review is local and reviewable; it does not post to GitHub.

0123 adds the local review boundary after the baby-fork scenario and passive graph export:

```text
GitHubProjectPublication + ContextGraphSnapshot + DotGraphExport -> GitHubPublicationReviewPacket
```

The review packet is the surface a human or later integration can inspect before a real external adapter posts anything back to GitHub Projects.

## Boundary

No GitHub API/HTTP/socket import in GitHubPublicationReview.

The module is data-only and importable. It combines:

- publication refs from `GitHubProjectPublication`;
- graph snapshot refs from `ContextGraphSnapshot`;
- deterministic DOT digest from `DotGraphExport`;
- bounded candidate summaries from the specialist result.

It produces a `GitHubPublicationReviewPacket` and an optional Markdown rendering. The packet is still pending by default. A future GitHub adapter may consume it only after explicit review/approval.

## Authority rules

SQLContextStore is durable context authority.

Qdrant is vector projection and retrieval, not context authority.

OpenVINO produces embeddings behind adapter.

LLM is specialist producer, not context authority.

Scheduler orchestrates context exploration jobs; it does not publish reviews itself.

MVTC remains future, not runtime in 0123.

## Non-goals

0123 does not add a GitHub client, token handling, webhook listener, background worker, watcher, OpenRC service, EventBus subscription, or Scheduler command. It only creates a deterministic local packet ready for a later adapter boundary.
