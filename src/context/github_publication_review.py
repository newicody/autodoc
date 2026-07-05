"""Local GitHub publication review packet boundary.

0123 turns a GitHubProjectPublication plus a passive context graph export into a
bounded review packet that a human or later external GitHub adapter can inspect.
It does not post to GitHub, open sockets, call HTTP APIs, subscribe to live buses,
or mutate scheduler state.

GitHub publication review is local and reviewable; it does not post to GitHub.
SQLContextStore is durable context authority.
Qdrant is vector projection and retrieval, not context authority.
OpenVINO produces embeddings behind adapter.
LLM is specialist producer, not context authority.
Scheduler orchestrates context exploration jobs; it does not publish reviews itself.
MVTC remains future, not runtime in 0123.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re

from context.context_graph_export import ContextGraphSnapshot, DotGraphExport
from context.github_project_scenario import GitHubCandidatePublication, GitHubProjectScenarioPacket

_REVIEW_ITEM_SCHEMA = "missipy.github_project.publication_review_item.v1"
_REVIEW_SCHEMA = "missipy.github_project.publication_review.v1"
_RENDER_SCHEMA = "missipy.github_project.publication_review_markdown.v1"
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_ALLOWED_REVIEW_PREFIXES = ("github-review:",)
_ALLOWED_GRAPH_PREFIXES = ("ctx-graph:",)
_ALLOWED_GITHUB_PREFIXES = ("github:",)
_ALLOWED_SQL_PREFIXES = ("sql:",)
_ALLOWED_RESULT_PREFIXES = ("specialist:", "ctx-result:")
_ALLOWED_EVIDENCE_PREFIXES = ("sql:", "qdrant:", "ctx:", "ctx-fragment:")
_ALLOWED_ACTION_PREFIXES = ("github:", "specialist:", "artifact:", "ctx-result:")
_ALLOWED_DECISIONS = frozenset({"pending", "approve", "revise", "reject"})


@dataclass(frozen=True, slots=True)
class GitHubPublicationReviewPolicy:
    """Bounds for local review material before any external publication."""

    max_candidates: int = 4
    max_summary_chars: int = 1_024
    max_body_chars: int = 4_096
    include_graph_digest: bool = True
    default_decision: str = "pending"

    def __post_init__(self) -> None:
        if self.max_candidates <= 0:
            raise ValueError("max_candidates must be > 0")
        if self.max_summary_chars <= 0:
            raise ValueError("max_summary_chars must be > 0")
        if self.max_body_chars <= 0:
            raise ValueError("max_body_chars must be > 0")
        if self.default_decision not in _ALLOWED_DECISIONS:
            raise ValueError("default_decision must be pending/approve/revise/reject")


@dataclass(frozen=True, slots=True)
class GitHubPublicationReviewItem:
    """One reviewable specialist candidate for a GitHub project item."""

    candidate_ref: str
    title: str
    summary: str
    evidence_refs: tuple[str, ...]
    action_refs: tuple[str, ...] = ()
    confidence: float = 0.0
    decision: str = "pending"
    truncated: bool = False
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("candidate_ref", self.candidate_ref, required_prefixes=("specialist:",))
        _require_non_empty("title", self.title)
        _require_non_empty("summary", self.summary)
        object.__setattr__(self, "evidence_refs", _normalize_refs("evidence_refs", self.evidence_refs))
        for ref in self.evidence_refs:
            if not ref.startswith(_ALLOWED_EVIDENCE_PREFIXES):
                raise ValueError("evidence_refs must point to SQL/Qdrant/context refs")
        object.__setattr__(self, "action_refs", _normalize_refs("action_refs", self.action_refs, allow_empty=True))
        for ref in self.action_refs:
            if not ref.startswith(_ALLOWED_ACTION_PREFIXES):
                raise ValueError("action_refs must be github/specialist/artifact/ctx-result refs")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.decision not in _ALLOWED_DECISIONS:
            raise ValueError("decision must be pending/approve/revise/reject")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _REVIEW_ITEM_SCHEMA,
            "candidate_ref": self.candidate_ref,
            "title": self.title,
            "summary": self.summary,
            "evidence_refs": list(self.evidence_refs),
            "action_refs": list(self.action_refs),
            "confidence": self.confidence,
            "decision": self.decision,
            "truncated": self.truncated,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class GitHubPublicationReviewPacket:
    """Local review packet for a future GitHub Project publication adapter."""

    review_ref: str
    publication_ref: str
    project_ref: str
    item_ref: str
    artifact_ref: str
    sql_context_ref: str
    specialist_result_ref: str
    graph_snapshot_ref: str
    dot_digest: str
    title: str
    body: str
    candidates: tuple[GitHubPublicationReviewItem, ...]
    status: str = "pending"
    target_ref: str = "github:project-result:pending"
    capped: bool = False
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("review_ref", self.review_ref, required_prefixes=_ALLOWED_REVIEW_PREFIXES)
        _require_typed_ref("publication_ref", self.publication_ref, required_prefixes=_ALLOWED_GITHUB_PREFIXES)
        _require_typed_ref("project_ref", self.project_ref, required_prefixes=_ALLOWED_GITHUB_PREFIXES)
        _require_typed_ref("item_ref", self.item_ref, required_prefixes=_ALLOWED_GITHUB_PREFIXES)
        _require_typed_ref("artifact_ref", self.artifact_ref, required_prefixes=_ALLOWED_GITHUB_PREFIXES)
        _require_typed_ref("sql_context_ref", self.sql_context_ref, required_prefixes=_ALLOWED_SQL_PREFIXES)
        _require_typed_ref("specialist_result_ref", self.specialist_result_ref, required_prefixes=_ALLOWED_RESULT_PREFIXES)
        _require_typed_ref("graph_snapshot_ref", self.graph_snapshot_ref, required_prefixes=_ALLOWED_GRAPH_PREFIXES)
        _require_digest("dot_digest", self.dot_digest)
        _require_non_empty("title", self.title)
        _require_non_empty("body", self.body)
        if not self.candidates:
            raise ValueError("candidates must not be empty")
        object.__setattr__(self, "candidates", tuple(self.candidates))
        if self.status not in _ALLOWED_DECISIONS:
            raise ValueError("status must be pending/approve/revise/reject")
        _require_typed_ref("target_ref", self.target_ref, required_prefixes=_ALLOWED_GITHUB_PREFIXES)
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def candidate_refs(self) -> tuple[str, ...]:
        return tuple(candidate.candidate_ref for candidate in self.candidates)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _REVIEW_SCHEMA,
            "review_ref": self.review_ref,
            "publication_ref": self.publication_ref,
            "project_ref": self.project_ref,
            "item_ref": self.item_ref,
            "artifact_ref": self.artifact_ref,
            "sql_context_ref": self.sql_context_ref,
            "specialist_result_ref": self.specialist_result_ref,
            "graph_snapshot_ref": self.graph_snapshot_ref,
            "dot_digest": self.dot_digest,
            "title": self.title,
            "body": self.body,
            "candidate_refs": list(self.candidate_refs),
            "status": self.status,
            "target_ref": self.target_ref,
            "capped": self.capped,
            "candidates": [candidate.to_mapping() for candidate in self.candidates],
            "metadata": dict(self.metadata),
            "runtime_import": "none; external GitHub adapter posts only after review",
        }


@dataclass(frozen=True, slots=True)
class GitHubPublicationReviewMarkdown:
    """Bounded Markdown rendering for local review surfaces."""

    review_ref: str
    markdown: str
    candidate_count: int

    def __post_init__(self) -> None:
        _require_typed_ref("review_ref", self.review_ref, required_prefixes=_ALLOWED_REVIEW_PREFIXES)
        _require_non_empty("markdown", self.markdown)
        if self.candidate_count <= 0:
            raise ValueError("candidate_count must be > 0")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _RENDER_SCHEMA,
            "review_ref": self.review_ref,
            "candidate_count": self.candidate_count,
            "format": "markdown",
            "markdown": self.markdown,
        }


def build_github_publication_review(
    packet: GitHubProjectScenarioPacket,
    graph: ContextGraphSnapshot,
    dot_export: DotGraphExport,
    *,
    policy: GitHubPublicationReviewPolicy | None = None,
) -> GitHubPublicationReviewPacket:
    """Build a local review packet; no GitHub API call is performed."""

    effective = policy or GitHubPublicationReviewPolicy()
    publication = packet.publication
    _validate_graph_matches_publication(graph, publication.publication_ref)
    if dot_export.snapshot_ref != graph.snapshot_ref:
        raise ValueError("dot_export snapshot_ref must match graph snapshot_ref")
    selected = publication.candidates[: effective.max_candidates]
    review_items = tuple(_review_item(candidate, effective) for candidate in selected)
    capped = publication.capped or len(publication.candidates) > len(selected)
    body, body_truncated = _truncate(publication.body, effective.max_body_chars)
    identity = f"{publication.publication_ref}\0{graph.snapshot_ref}\0{dot_export.dot}"
    metadata = (
        ("graph_snapshot_ref", graph.snapshot_ref),
        ("dot_digest", _digest(dot_export.dot)),
        ("external_adapter", "required_after_review"),
        ("local_review_only", "true"),
    )
    if body_truncated:
        metadata = (*metadata, ("body_truncated", "true"))
    return GitHubPublicationReviewPacket(
        review_ref=f"github-review:publication:{_digest(identity)}",
        publication_ref=publication.publication_ref,
        project_ref=publication.project_ref,
        item_ref=publication.item_ref,
        artifact_ref=publication.artifact_ref,
        sql_context_ref=publication.sql_context_ref,
        specialist_result_ref=publication.specialist_result_ref,
        graph_snapshot_ref=graph.snapshot_ref,
        dot_digest=_digest(dot_export.dot),
        title=f"Review: {publication.title}",
        body=body,
        candidates=review_items,
        status=effective.default_decision,
        target_ref=publication.target_ref,
        capped=capped,
        metadata=metadata if effective.include_graph_digest else tuple(pair for pair in metadata if pair[0] != "dot_digest"),
    )


def render_github_publication_review_markdown(
    review: GitHubPublicationReviewPacket,
) -> GitHubPublicationReviewMarkdown:
    """Render a deterministic Markdown review without posting anywhere."""

    lines = [
        f"# {review.title}",
        "",
        f"Review status: {review.status}",
        "Publication is local and reviewable; it does not post to GitHub.",
        "External GitHub adapter required after approval.",
        "",
        "## Authority and refs",
        f"- SQLContextStore authority: `{review.sql_context_ref}`",
        f"- Qdrant graph/projection evidence digest: `{review.dot_digest}`",
        f"- Graph snapshot: `{review.graph_snapshot_ref}`",
        f"- Specialist result: `{review.specialist_result_ref}`",
        "",
        "## Publication body",
        review.body,
        "",
        "## Candidates",
    ]
    for index, candidate in enumerate(review.candidates, start=1):
        evidence = ", ".join(f"`{ref}`" for ref in candidate.evidence_refs)
        actions = ", ".join(f"`{ref}`" for ref in candidate.action_refs) or "none"
        lines.extend(
            [
                f"{index}. **{candidate.title}**",
                f"   - Ref: `{candidate.candidate_ref}`",
                f"   - Decision: {candidate.decision}",
                f"   - Confidence: {candidate.confidence:.2f}",
                f"   - Evidence: {evidence}",
                f"   - Actions: {actions}",
                f"   - Summary: {candidate.summary}",
            ]
        )
    return GitHubPublicationReviewMarkdown(
        review_ref=review.review_ref,
        markdown="\n".join(lines),
        candidate_count=len(review.candidates),
    )


def _review_item(
    candidate: GitHubCandidatePublication,
    policy: GitHubPublicationReviewPolicy,
) -> GitHubPublicationReviewItem:
    summary, truncated = _truncate(candidate.summary, policy.max_summary_chars)
    return GitHubPublicationReviewItem(
        candidate_ref=candidate.candidate_ref,
        title=candidate.title,
        summary=summary,
        evidence_refs=candidate.evidence_refs,
        action_refs=candidate.action_refs,
        confidence=candidate.confidence,
        decision=policy.default_decision,
        truncated=truncated or candidate.truncated,
        metadata=(("source", "github_project_publication"),),
    )


def _validate_graph_matches_publication(graph: ContextGraphSnapshot, publication_ref: str) -> None:
    if not any(node.ref == publication_ref for node in graph.nodes):
        raise ValueError("graph must contain the publication_ref")


def _truncate(value: str, max_chars: int) -> tuple[str, bool]:
    if len(value) <= max_chars:
        return value, False
    if max_chars <= 1:
        return value[:max_chars], True
    return value[: max_chars - 1] + "…", True


def _normalize_refs(name: str, values: tuple[str, ...], *, allow_empty: bool = False) -> tuple[str, ...]:
    normalized = tuple(values)
    if not normalized and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    for value in normalized:
        _require_typed_ref(name, value)
    return normalized


def _normalize_metadata(values: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    normalized: dict[str, str] = {}
    for key, value in values:
        _require_non_empty("metadata key", key)
        _require_non_empty("metadata value", value)
        normalized[key] = value
    return tuple(sorted(normalized.items()))


def _require_typed_ref(name: str, value: str, *, required_prefixes: tuple[str, ...] | None = None) -> None:
    _require_non_empty(name, value)
    if not _TYPED_REF_RE.match(value):
        raise ValueError(f"{name} must be a typed reference")
    if required_prefixes is not None and not value.startswith(required_prefixes):
        joined = ", ".join(required_prefixes)
        raise ValueError(f"{name} must start with one of: {joined}")


def _require_digest(name: str, value: str) -> None:
    _require_non_empty(name, value)
    if not re.match(r"^[0-9a-f]{16}$", value):
        raise ValueError(f"{name} must be a 16-character hex digest")


def _require_non_empty(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
