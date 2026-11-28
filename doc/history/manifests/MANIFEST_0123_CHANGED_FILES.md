# Manifest 0123 — GitHub publication review

Patch id: `0123-github_publication_review`

Changed files:

- `src/context/github_publication_review.py`
- `tests/runtime/test_github_publication_review.py`
- `tests/rules/test_github_publication_review_0123_rule.py`
- `doc/architecture/GITHUB_PUBLICATION_REVIEW_0123.md`
- `doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0123.md`
- `doc/docs/architecture/runtime/116_github_publication_review.dot`
- `doc/CHANGELOG_0123_GITHUB_PUBLICATION_REVIEW.md`
- `doc/manifests/MANIFEST_0123_CHANGED_FILES.md`
- `PHASE0123_TEST_REPORT.md`

Explicitly not changed: kernel scheduler/dispatcher/queue, policy engine, runtime manager, observability bus, and GitHub client surfaces.

Boundary notes:

- GitHub publication review is local and reviewable; it does not post to GitHub.
- No GitHub API/HTTP/socket import in GitHubPublicationReview.
- SQLContextStore is durable context authority.
- Qdrant is vector projection and retrieval, not context authority.
- OpenVINO produces embeddings behind adapter.
- LLM is specialist producer, not context authority.
- MVTC remains future, not runtime in 0123.
