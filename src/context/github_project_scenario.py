"""GitHub project context scenario contracts.

0121 models the baby-fork project loop without calling GitHub.  A fetched
GitHub artifact is converted into a SQL source candidate, the context planner
builds bounded variants, a specialist result proposes solution candidates, and
a publication packet can later be posted back by a separate GitHub adapter.

GitHubProjectScenario is data-only; no GitHub API/HTTP/socket runtime import.
SQLContextStore is durable context authority.
Qdrant is vector projection and retrieval, not context authority.
OpenVINO produces embeddings behind adapter.
LLM is specialist producer, not context authority.
MVTC remains future, not runtime in 0121.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re

from context.context_variation_core import ContextExplorationPlan, ContextVariationObjective
from context.sql_context_store import SqlContextRecord, build_sql_context_record
from inference.llm_specialist_adapter import LLMSolutionCandidate, LLMSpecialistResult

_ARTIFACT_SCHEMA = "missipy.github_project.artifact.v1"
_SOURCE_SCHEMA = "missipy.github_project.source_candidate.v1"
_PUBLICATION_SCHEMA = "missipy.github_project.publication.v1"
_SCENARIO_SCHEMA = "missipy.github_project.scenario.v1"
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_ALLOWED_GITHUB_PREFIXES = ("github:",)
_ALLOWED_SQL_PREFIXES = ("sql:",)
_ALLOWED_RESULT_PREFIXES = ("specialist:", "ctx-result:")
_ALLOWED_PUBLICATION_TARGETS = ("github:",)


@dataclass(frozen=True, slots=True)
class GitHubProjectArtifact:
    """Fetched project artifact represented without GitHub runtime coupling."""

    artifact_ref: str
    project_ref: str
    item_ref: str
    title: str
    body: str
    author_ref: str | None = None
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("artifact_ref", self.artifact_ref, required_prefixes=_ALLOWED_GITHUB_PREFIXES)
        _require_typed_ref("project_ref", self.project_ref, required_prefixes=_ALLOWED_GITHUB_PREFIXES)
        _require_typed_ref("item_ref", self.item_ref, required_prefixes=_ALLOWED_GITHUB_PREFIXES)
        _require_non_empty("title", self.title)
        _require_non_empty("body", self.body)
        if self.author_ref is not None:
            _require_typed_ref("author_ref", self.author_ref, required_prefixes=_ALLOWED_GITHUB_PREFIXES)
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _ARTIFACT_SCHEMA,
            "artifact_ref": self.artifact_ref,
            "project_ref": self.project_ref,
            "item_ref": self.item_ref,
            "title": self.title,
            "body": self.body,
            "author_ref": self.author_ref,
            "metadata": dict(self.metadata),
            "runtime_import": "external GitHub adapter only",
        }


@dataclass(frozen=True, slots=True)
class GitHubSourceCandidate:
    """SQL-ready source candidate derived from a GitHub project artifact."""

    source_ref: str
    artifact: GitHubProjectArtifact
    sql_record: SqlContextRecord

    def __post_init__(self) -> None:
        _require_typed_ref("source_ref", self.source_ref, required_prefixes=("artifact:",))
        if not self.sql_record.context_ref.startswith(_ALLOWED_SQL_PREFIXES):
            raise ValueError("sql_record must use a sql:* context_ref")
        if self.sql_record.kind != "github_artifact":
            raise ValueError("sql_record kind must be github_artifact")
        if self.sql_record.parent_ref != self.artifact.item_ref:
            raise ValueError("sql_record parent_ref must point to artifact item_ref")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _SOURCE_SCHEMA,
            "source_ref": self.source_ref,
            "artifact": self.artifact.to_mapping(),
            "sql_context_ref": self.sql_record.context_ref,
            "sql_record": self.sql_record.to_mapping(),
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectPublicationPolicy:
    """Bounds for a publication packet that a future GitHub adapter can post."""

    max_candidates: int = 4
    max_summary_chars: int = 2_048

    def __post_init__(self) -> None:
        if self.max_candidates <= 0:
            raise ValueError("max_candidates must be > 0")
        if self.max_summary_chars <= 0:
            raise ValueError("max_summary_chars must be > 0")


@dataclass(frozen=True, slots=True)
class GitHubCandidatePublication:
    """One solution candidate serialized for GitHub project publication."""

    candidate_ref: str
    title: str
    summary: str
    evidence_refs: tuple[str, ...]
    action_refs: tuple[str, ...] = ()
    confidence: float = 0.0
    truncated: bool = False

    def __post_init__(self) -> None:
        _require_typed_ref("candidate_ref", self.candidate_ref, required_prefixes=("specialist:",))
        _require_non_empty("title", self.title)
        _require_non_empty("summary", self.summary)
        object.__setattr__(self, "evidence_refs", _normalize_refs("evidence_refs", self.evidence_refs))
        object.__setattr__(self, "action_refs", _normalize_refs("action_refs", self.action_refs, allow_empty=True))
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_mapping(self) -> dict[str, object]:
        return {
            "candidate_ref": self.candidate_ref,
            "title": self.title,
            "summary": self.summary,
            "evidence_refs": list(self.evidence_refs),
            "action_refs": list(self.action_refs),
            "confidence": self.confidence,
            "truncated": self.truncated,
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectPublication:
    """Publication packet for later GitHub Project synchronization."""

    publication_ref: str
    project_ref: str
    item_ref: str
    artifact_ref: str
    sql_context_ref: str
    plan_id: str
    specialist_result_ref: str
    title: str
    body: str
    candidates: tuple[GitHubCandidatePublication, ...]
    target_ref: str = "github:project-result:pending"
    capped: bool = False

    def __post_init__(self) -> None:
        _require_typed_ref("publication_ref", self.publication_ref, required_prefixes=("github:",))
        _require_typed_ref("project_ref", self.project_ref, required_prefixes=_ALLOWED_PUBLICATION_TARGETS)
        _require_typed_ref("item_ref", self.item_ref, required_prefixes=_ALLOWED_PUBLICATION_TARGETS)
        _require_typed_ref("artifact_ref", self.artifact_ref, required_prefixes=_ALLOWED_PUBLICATION_TARGETS)
        _require_typed_ref("sql_context_ref", self.sql_context_ref, required_prefixes=_ALLOWED_SQL_PREFIXES)
        _require_non_empty("plan_id", self.plan_id)
        _require_typed_ref("specialist_result_ref", self.specialist_result_ref, required_prefixes=_ALLOWED_RESULT_PREFIXES)
        _require_non_empty("title", self.title)
        _require_non_empty("body", self.body)
        if not self.candidates:
            raise ValueError("candidates must not be empty")
        object.__setattr__(self, "candidates", tuple(self.candidates))
        _require_typed_ref("target_ref", self.target_ref, required_prefixes=_ALLOWED_PUBLICATION_TARGETS)

    @property
    def candidate_refs(self) -> tuple[str, ...]:
        return tuple(candidate.candidate_ref for candidate in self.candidates)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _PUBLICATION_SCHEMA,
            "publication_ref": self.publication_ref,
            "project_ref": self.project_ref,
            "item_ref": self.item_ref,
            "artifact_ref": self.artifact_ref,
            "sql_context_ref": self.sql_context_ref,
            "plan_id": self.plan_id,
            "specialist_result_ref": self.specialist_result_ref,
            "title": self.title,
            "body": self.body,
            "candidate_refs": list(self.candidate_refs),
            "target_ref": self.target_ref,
            "capped": self.capped,
            "candidates": [candidate.to_mapping() for candidate in self.candidates],
            "runtime_import": "external GitHub adapter only",
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectScenarioPacket:
    """End-to-end data packet for the GitHub baby-fork context loop."""

    artifact: GitHubProjectArtifact
    source_candidate: GitHubSourceCandidate
    objective: ContextVariationObjective
    plan: ContextExplorationPlan
    specialist_result: LLMSpecialistResult
    publication: GitHubProjectPublication

    def __post_init__(self) -> None:
        if self.source_candidate.artifact != self.artifact:
            raise ValueError("source_candidate must wrap packet artifact")
        if self.objective.source_ref != self.source_candidate.sql_record.context_ref:
            raise ValueError("objective source_ref must point to SQL source candidate")
        if self.plan.objective != self.objective:
            raise ValueError("plan objective must match packet objective")
        if self.publication.specialist_result_ref != self.specialist_result.result_ref:
            raise ValueError("publication must reference specialist_result")
        if self.publication.sql_context_ref != self.source_candidate.sql_record.context_ref:
            raise ValueError("publication must reference SQL context authority")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _SCENARIO_SCHEMA,
            "artifact": self.artifact.to_mapping(),
            "source_candidate": self.source_candidate.to_mapping(),
            "objective": self.objective.to_mapping(),
            "plan": self.plan.to_mapping(),
            "specialist_result": self.specialist_result.to_mapping(),
            "publication": self.publication.to_mapping(),
        }


def build_github_source_candidate(artifact: GitHubProjectArtifact) -> GitHubSourceCandidate:
    """Convert a GitHub artifact into a SQL-ready source candidate."""

    identity = f"{artifact.project_ref}\0{artifact.item_ref}\0{artifact.artifact_ref}"
    metadata = _merge_metadata(
        artifact.metadata,
        (
            ("source_system", "github_project"),
            ("artifact_ref", artifact.artifact_ref),
            ("project_ref", artifact.project_ref),
            ("item_ref", artifact.item_ref),
        ),
    )
    if artifact.author_ref is not None:
        metadata = _merge_metadata(metadata, (("author_ref", artifact.author_ref),))
    sql_record = build_sql_context_record(
        kind="github_artifact",
        identity=identity,
        title=artifact.title,
        body=artifact.body,
        parent_ref=artifact.item_ref,
        metadata=metadata,
    )
    return GitHubSourceCandidate(
        source_ref=f"artifact:github-source:{_digest(identity)}",
        artifact=artifact,
        sql_record=sql_record,
    )


def build_github_context_objective(
    source_candidate: GitHubSourceCandidate,
    *,
    title: str | None = None,
    statement: str | None = None,
) -> ContextVariationObjective:
    """Build the context objective that starts local exploration."""

    artifact = source_candidate.artifact
    objective_title = title or artifact.title
    objective_statement = statement or artifact.body
    identity = f"{source_candidate.sql_record.context_ref}\0{objective_title}\0{objective_statement}"
    return ContextVariationObjective(
        objective_id=f"github-objective-{_digest(identity)}",
        title=objective_title,
        statement=objective_statement,
        source_ref=source_candidate.sql_record.context_ref,
        parent_context_ref=artifact.item_ref,
    )


def build_github_project_publication(
    *,
    artifact: GitHubProjectArtifact,
    source_candidate: GitHubSourceCandidate,
    plan: ContextExplorationPlan,
    specialist_result: LLMSpecialistResult,
    policy: GitHubProjectPublicationPolicy | None = None,
) -> GitHubProjectPublication:
    """Build a bounded publication packet from specialist candidates."""

    if plan.objective.source_ref != source_candidate.sql_record.context_ref:
        raise ValueError("plan objective must originate from source_candidate SQL ref")
    effective = policy or GitHubProjectPublicationPolicy()
    selected = specialist_result.candidates[: effective.max_candidates]
    publications = tuple(_candidate_publication(candidate, effective) for candidate in selected)
    capped = specialist_result.capped or len(specialist_result.candidates) > len(selected)
    title = f"Autodoc context result: {artifact.title}"
    body = _publication_body(plan, specialist_result, publications)
    identity = f"{artifact.item_ref}\0{plan.plan_id}\0{specialist_result.result_ref}"
    return GitHubProjectPublication(
        publication_ref=f"github:project-publication:{_digest(identity)}",
        project_ref=artifact.project_ref,
        item_ref=artifact.item_ref,
        artifact_ref=artifact.artifact_ref,
        sql_context_ref=source_candidate.sql_record.context_ref,
        plan_id=plan.plan_id,
        specialist_result_ref=specialist_result.result_ref,
        title=title,
        body=body,
        candidates=publications,
        target_ref=f"github:project-result:{_digest(artifact.item_ref)}",
        capped=capped,
    )


def build_github_project_scenario_packet(
    *,
    artifact: GitHubProjectArtifact,
    plan: ContextExplorationPlan,
    specialist_result: LLMSpecialistResult,
    policy: GitHubProjectPublicationPolicy | None = None,
) -> GitHubProjectScenarioPacket:
    """Build the full reference-only GitHub project scenario packet."""

    source_candidate = build_github_source_candidate(artifact)
    objective = build_github_context_objective(source_candidate)
    if plan.objective != objective:
        raise ValueError("plan objective must be built from the GitHub source candidate")
    publication = build_github_project_publication(
        artifact=artifact,
        source_candidate=source_candidate,
        plan=plan,
        specialist_result=specialist_result,
        policy=policy,
    )
    return GitHubProjectScenarioPacket(
        artifact=artifact,
        source_candidate=source_candidate,
        objective=objective,
        plan=plan,
        specialist_result=specialist_result,
        publication=publication,
    )


def _candidate_publication(
    candidate: LLMSolutionCandidate,
    policy: GitHubProjectPublicationPolicy,
) -> GitHubCandidatePublication:
    summary, truncated = _truncate(candidate.summary, policy.max_summary_chars)
    return GitHubCandidatePublication(
        candidate_ref=candidate.candidate_ref,
        title=candidate.title,
        summary=summary,
        evidence_refs=candidate.evidence_refs,
        action_refs=candidate.action_refs,
        confidence=candidate.confidence,
        truncated=truncated,
    )


def _publication_body(
    plan: ContextExplorationPlan,
    specialist_result: LLMSpecialistResult,
    candidates: tuple[GitHubCandidatePublication, ...],
) -> str:
    lines = [
        "Autodoc local context exploration result.",
        f"Plan: {plan.plan_id}",
        f"Specialist result: {specialist_result.result_ref}",
        "Candidates:",
    ]
    for index, candidate in enumerate(candidates, start=1):
        lines.append(f"{index}. {candidate.title} ({candidate.candidate_ref})")
    return "\n".join(lines)


def _truncate(value: str, max_chars: int) -> tuple[str, bool]:
    if len(value) <= max_chars:
        return value, False
    return value[:max_chars], True


def _merge_metadata(*groups: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    merged: dict[str, str] = {}
    for group in groups:
        for key, value in group:
            _require_non_empty("metadata key", key)
            _require_non_empty("metadata value", value)
            merged[key] = value
    return tuple(sorted(merged.items()))


def _normalize_metadata(values: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    return _merge_metadata(values)


def _normalize_refs(name: str, values: tuple[str, ...], *, allow_empty: bool = False) -> tuple[str, ...]:
    normalized = tuple(values)
    if not normalized and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    for value in normalized:
        _require_typed_ref(name, value)
    return normalized


def _require_typed_ref(name: str, value: str, *, required_prefixes: tuple[str, ...] | None = None) -> None:
    _require_non_empty(name, value)
    if not _TYPED_REF_RE.match(value):
        raise ValueError(f"{name} must be a typed reference")
    if required_prefixes is not None and not value.startswith(required_prefixes):
        raise ValueError(f"{name} must start with one of {', '.join(required_prefixes)}")


def _require_non_empty(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
