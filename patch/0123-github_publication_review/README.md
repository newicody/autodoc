# 0123-github_publication_review

Adds a local GitHub publication review packet boundary.

The patch introduces `src/context/github_publication_review.py`, which turns a
`GitHubProjectPublication`, `ContextGraphSnapshot`, and `DotGraphExport` into a
reviewable `GitHubPublicationReviewPacket` plus deterministic Markdown rendering.
It is a local review surface only; a future external GitHub adapter may post the
packet after explicit approval.

It does not import GitHub clients, HTTP clients, sockets, Qdrant, OpenVINO,
PostgreSQL, LLM SDKs, Scheduler, Dispatcher, PolicyEngine, EventBus, or
RouteRuntimeManager.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_github_publication_review.py
PYTHONPATH=src:. pytest -q tests/rules/test_github_publication_review_0123_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
