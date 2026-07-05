"""Server-oriented specialist deliberation cycle contracts.

0124 corrects the boundary around GitHub and specialist work.  GitHub artifact
exchange only moves artifacts in and final artifacts out.  The server-local
cycle performs orientation, asks specialists for preliminary opinions, refines
new demands, performs as many rounds as needed, and only then prepares a final
artifact envelope for a later adapter.

GitHub artifact exchange only moves artifacts in and final artifacts out.
ServerOrientation drives specialist deliberation before publication.
Specialist preliminary opinions are recomposed into refined demands.
Specialist bus statistics feed passive supervision and VisPy, not GitHub.
Final GitHub publication happens only after local convergence.
SQLContextStore is durable context authority.
Qdrant is vector projection and retrieval, not context authority.
OpenVINO produces embeddings behind adapter.
LLM is specialist producer, not context authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re

from context.github_project_scenario import GitHubProjectArtifact, GitHubSourceCandidate
from context.specialist_liaison_synthesis import SpecialistLiaisonSynthesis

_ORIENTATION_SCHEMA = "missipy.deliberation.server_orientation.v1"
_OPINION_SCHEMA = "missipy.deliberation.specialist_preliminary_opinion.v1"
_DEMAND_SCHEMA = "missipy.deliberation.refined_specialist_demand.v1"
_ROUND_SCHEMA = "missipy.deliberation.round.v1"
_STATS_SCHEMA = "missipy.deliberation.bus_statistics.v1"
_FINAL_ARTIFACT_SCHEMA = "missipy.deliberation.final_artifact_envelope.v1"
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_ALLOWED_GITHUB_PREFIXES = ("github:",)
_ALLOWED_ARTIFACT_PREFIXES = ("artifact:", "github:")
_ALLOWED_SQL_PREFIXES = ("sql:",)
_ALLOWED_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_ALLOWED_CONTEXT_PREFIXES = ("sql:", "ctx:", "ctx-result:", "ctx-fragment:", "qdrant:", "artifact:")
_ALLOWED_BUS_PREFIXES = ("bus:", "specialist-path:")
_ALLOWED_VALIDATION_PREFIXES = ("artifact:", "sql:", "ctx-result:", "specialist:")
_ALLOWED_REVIEW_PREFIXES = ("specialist:", "ctx-review:", "artifact:")
_ALLOWED_FINAL_TARGET_PREFIXES = ("github:", "artifact:", "local:", "publication:")
_STANCES = (
    "possible",
    "impossible",
    "risky",
    "better_alternative",
    "needs_context",
    "needs_specialist",
    "analysis_signal",
)
_CONVERGENCE_STATES = (
    "needs_more_opinions",
    "needs_refinement",
    "ready_for_production",
    "ready_for_final_synthesis",
    "blocked",
)
_DEPTHS = ("shallow", "standard", "deep", "audit")


@dataclass(frozen=True, slots=True)
class DeliberationPolicy:
    """Bounds for server-local deliberation planning."""

    max_specialists: int = 8
    max_document_kinds: int = 6
    max_directives: int = 12
    max_opinions_per_round: int = 16
    max_refined_demands: int = 16
    max_final_body_chars: int = 8_192

    def __post_init__(self) -> None:
        for field_name in (
            "max_specialists",
            "max_document_kinds",
            "max_directives",
            "max_opinions_per_round",
            "max_refined_demands",
            "max_final_body_chars",
        ):
            if getattr(self, field_name) <= 0:
                raise ValueError(f"{field_name} must be > 0")


@dataclass(frozen=True, slots=True)
class ServerOrientation:
    """First server-local orientation extracted from an artifact."""

    orientation_ref: str
    artifact_ref: str
    source_ref: str
    sql_context_ref: str
    title: str
    intent: str
    requested_specialist_refs: tuple[str, ...]
    requested_document_kinds: tuple[str, ...]
    do_directives: tuple[str, ...] = ()
    avoid_directives: tuple[str, ...] = ()
    context_refs: tuple[str, ...] = ()
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("orientation_ref", self.orientation_ref, required_prefixes=("orientation:",))
        _require_typed_ref("artifact_ref", self.artifact_ref, required_prefixes=_ALLOWED_ARTIFACT_PREFIXES)
        _require_typed_ref("source_ref", self.source_ref, required_prefixes=("artifact:",))
        _require_typed_ref("sql_context_ref", self.sql_context_ref, required_prefixes=_ALLOWED_SQL_PREFIXES)
        _require_non_empty("title", self.title)
        _require_non_empty("intent", self.intent)
        object.__setattr__(
            self,
            "requested_specialist_refs",
            _normalize_refs(
                "requested_specialist_refs",
                self.requested_specialist_refs,
                required_prefixes=_ALLOWED_SPECIALIST_PREFIXES,
            ),
        )
        object.__setattr__(self, "requested_document_kinds", _normalize_texts("requested_document_kinds", self.requested_document_kinds))
        object.__setattr__(self, "do_directives", _normalize_texts("do_directives", self.do_directives, allow_empty=True))
        object.__setattr__(self, "avoid_directives", _normalize_texts("avoid_directives", self.avoid_directives, allow_empty=True))
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs("context_refs", self.context_refs, allow_empty=True, required_prefixes=_ALLOWED_CONTEXT_PREFIXES),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _ORIENTATION_SCHEMA,
            "orientation_ref": self.orientation_ref,
            "artifact_ref": self.artifact_ref,
            "source_ref": self.source_ref,
            "sql_context_ref": self.sql_context_ref,
            "title": self.title,
            "intent": self.intent,
            "requested_specialist_refs": list(self.requested_specialist_refs),
            "requested_document_kinds": list(self.requested_document_kinds),
            "do_directives": list(self.do_directives),
            "avoid_directives": list(self.avoid_directives),
            "context_refs": list(self.context_refs),
            "metadata": dict(self.metadata),
            "github_exchange_role": "artifact exchange only",
            "publication_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistPreliminaryOpinion:
    """First opinion a specialist returns before real production starts."""

    opinion_ref: str
    orientation_ref: str
    specialist_ref: str
    stance: str
    summary: str
    recommendation: str
    evidence_refs: tuple[str, ...] = ()
    requested_context_refs: tuple[str, ...] = ()
    proposed_specialist_refs: tuple[str, ...] = ()
    proposed_document_kinds: tuple[str, ...] = ()
    context_delta_refs: tuple[str, ...] = ()
    review_request_refs: tuple[str, ...] = ()
    validation_refs: tuple[str, ...] = ()
    bus_observation_refs: tuple[str, ...] = ()
    confidence: float = 0.0

    def __post_init__(self) -> None:
        _require_typed_ref("opinion_ref", self.opinion_ref, required_prefixes=("specialist-opinion:",))
        _require_typed_ref("orientation_ref", self.orientation_ref, required_prefixes=("orientation:",))
        _require_typed_ref("specialist_ref", self.specialist_ref, required_prefixes=_ALLOWED_SPECIALIST_PREFIXES)
        if self.stance not in _STANCES:
            raise ValueError("stance must be one of: " + ", ".join(_STANCES))
        _require_non_empty("summary", self.summary)
        _require_non_empty("recommendation", self.recommendation)
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs("evidence_refs", self.evidence_refs, allow_empty=True, required_prefixes=_ALLOWED_CONTEXT_PREFIXES),
        )
        object.__setattr__(
            self,
            "requested_context_refs",
            _normalize_refs("requested_context_refs", self.requested_context_refs, allow_empty=True, required_prefixes=_ALLOWED_CONTEXT_PREFIXES),
        )
        object.__setattr__(
            self,
            "proposed_specialist_refs",
            _normalize_refs("proposed_specialist_refs", self.proposed_specialist_refs, allow_empty=True, required_prefixes=_ALLOWED_SPECIALIST_PREFIXES),
        )
        object.__setattr__(self, "proposed_document_kinds", _normalize_texts("proposed_document_kinds", self.proposed_document_kinds, allow_empty=True))
        object.__setattr__(
            self,
            "context_delta_refs",
            _normalize_refs("context_delta_refs", self.context_delta_refs, allow_empty=True, required_prefixes=("ctx-result:", "ctx:", "sql:")),
        )
        object.__setattr__(
            self,
            "review_request_refs",
            _normalize_refs("review_request_refs", self.review_request_refs, allow_empty=True, required_prefixes=_ALLOWED_REVIEW_PREFIXES),
        )
        object.__setattr__(
            self,
            "validation_refs",
            _normalize_refs("validation_refs", self.validation_refs, allow_empty=True, required_prefixes=_ALLOWED_VALIDATION_PREFIXES),
        )
        object.__setattr__(
            self,
            "bus_observation_refs",
            _normalize_refs("bus_observation_refs", self.bus_observation_refs, allow_empty=True, required_prefixes=_ALLOWED_BUS_PREFIXES),
        )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _OPINION_SCHEMA,
            "opinion_ref": self.opinion_ref,
            "orientation_ref": self.orientation_ref,
            "specialist_ref": self.specialist_ref,
            "stance": self.stance,
            "summary": self.summary,
            "recommendation": self.recommendation,
            "evidence_refs": list(self.evidence_refs),
            "requested_context_refs": list(self.requested_context_refs),
            "proposed_specialist_refs": list(self.proposed_specialist_refs),
            "proposed_document_kinds": list(self.proposed_document_kinds),
            "context_delta_refs": list(self.context_delta_refs),
            "review_request_refs": list(self.review_request_refs),
            "validation_refs": list(self.validation_refs),
            "bus_observation_refs": list(self.bus_observation_refs),
            "confidence": self.confidence,
            "publication_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class RefinedSpecialistDemand:
    """A more precise demand produced after recomposing preliminary opinions."""

    demand_ref: str
    orientation_ref: str
    source_opinion_refs: tuple[str, ...]
    target_specialist_ref: str
    title: str
    prompt: str
    requested_output_kind: str
    depth: str = "standard"
    input_refs: tuple[str, ...] = ()
    context_refs: tuple[str, ...] = ()
    review_request_refs: tuple[str, ...] = ()
    validation_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_typed_ref("demand_ref", self.demand_ref, required_prefixes=("specialist-demand:",))
        _require_typed_ref("orientation_ref", self.orientation_ref, required_prefixes=("orientation:",))
        object.__setattr__(
            self,
            "source_opinion_refs",
            _normalize_refs("source_opinion_refs", self.source_opinion_refs, required_prefixes=("specialist-opinion:",)),
        )
        _require_typed_ref("target_specialist_ref", self.target_specialist_ref, required_prefixes=_ALLOWED_SPECIALIST_PREFIXES)
        _require_non_empty("title", self.title)
        _require_non_empty("prompt", self.prompt)
        _require_non_empty("requested_output_kind", self.requested_output_kind)
        if self.depth not in _DEPTHS:
            raise ValueError("depth must be shallow, standard, deep, or audit")
        object.__setattr__(
            self,
            "input_refs",
            _normalize_refs("input_refs", self.input_refs, allow_empty=True, required_prefixes=_ALLOWED_CONTEXT_PREFIXES),
        )
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs("context_refs", self.context_refs, allow_empty=True, required_prefixes=_ALLOWED_CONTEXT_PREFIXES),
        )
        object.__setattr__(
            self,
            "review_request_refs",
            _normalize_refs("review_request_refs", self.review_request_refs, allow_empty=True, required_prefixes=_ALLOWED_REVIEW_PREFIXES),
        )
        object.__setattr__(
            self,
            "validation_refs",
            _normalize_refs("validation_refs", self.validation_refs, allow_empty=True, required_prefixes=_ALLOWED_VALIDATION_PREFIXES),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _DEMAND_SCHEMA,
            "demand_ref": self.demand_ref,
            "orientation_ref": self.orientation_ref,
            "source_opinion_refs": list(self.source_opinion_refs),
            "target_specialist_ref": self.target_specialist_ref,
            "title": self.title,
            "prompt": self.prompt,
            "requested_output_kind": self.requested_output_kind,
            "depth": self.depth,
            "input_refs": list(self.input_refs),
            "context_refs": list(self.context_refs),
            "review_request_refs": list(self.review_request_refs),
            "validation_refs": list(self.validation_refs),
            "publication_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class DeliberationRound:
    """One local server/specialist deliberation round."""

    round_ref: str
    round_index: int
    orientation: ServerOrientation
    opinions: tuple[SpecialistPreliminaryOpinion, ...]
    refined_demands: tuple[RefinedSpecialistDemand, ...]
    convergence_state: str
    bus_observation_refs: tuple[str, ...] = ()
    needs_next_round: bool = True

    def __post_init__(self) -> None:
        _require_typed_ref("round_ref", self.round_ref, required_prefixes=("deliberation-round:",))
        if self.round_index < 0:
            raise ValueError("round_index must be >= 0")
        if self.convergence_state not in _CONVERGENCE_STATES:
            raise ValueError("convergence_state must be one of: " + ", ".join(_CONVERGENCE_STATES))
        object.__setattr__(self, "opinions", tuple(self.opinions))
        object.__setattr__(self, "refined_demands", tuple(self.refined_demands))
        for opinion in self.opinions:
            if opinion.orientation_ref != self.orientation.orientation_ref:
                raise ValueError("opinion orientation_ref must match round orientation")
        for demand in self.refined_demands:
            if demand.orientation_ref != self.orientation.orientation_ref:
                raise ValueError("demand orientation_ref must match round orientation")
        object.__setattr__(
            self,
            "bus_observation_refs",
            _normalize_refs("bus_observation_refs", self.bus_observation_refs, allow_empty=True, required_prefixes=_ALLOWED_BUS_PREFIXES),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _ROUND_SCHEMA,
            "round_ref": self.round_ref,
            "round_index": self.round_index,
            "orientation_ref": self.orientation.orientation_ref,
            "opinion_refs": [opinion.opinion_ref for opinion in self.opinions],
            "refined_demand_refs": [demand.demand_ref for demand in self.refined_demands],
            "convergence_state": self.convergence_state,
            "needs_next_round": self.needs_next_round,
            "bus_observation_refs": list(self.bus_observation_refs),
            "github_exchange_role": "artifact exchange only",
            "observation_only": True,
            "publication_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistBusStatistics:
    """Local statistics for passive supervision and VisPy views."""

    stats_ref: str
    round_refs: tuple[str, ...]
    opinion_count: int
    refined_demand_count: int
    bus_observation_count: int
    requested_context_count: int
    review_request_count: int
    validation_ref_count: int
    specialist_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_typed_ref("stats_ref", self.stats_ref, required_prefixes=("bus-stats:",))
        object.__setattr__(self, "round_refs", _normalize_refs("round_refs", self.round_refs, required_prefixes=("deliberation-round:",)))
        object.__setattr__(
            self,
            "specialist_refs",
            _normalize_refs("specialist_refs", self.specialist_refs, allow_empty=True, required_prefixes=_ALLOWED_SPECIALIST_PREFIXES),
        )
        for field_name in (
            "opinion_count",
            "refined_demand_count",
            "bus_observation_count",
            "requested_context_count",
            "review_request_count",
            "validation_ref_count",
        ):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} must be >= 0")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _STATS_SCHEMA,
            "stats_ref": self.stats_ref,
            "round_refs": list(self.round_refs),
            "opinion_count": self.opinion_count,
            "refined_demand_count": self.refined_demand_count,
            "bus_observation_count": self.bus_observation_count,
            "requested_context_count": self.requested_context_count,
            "review_request_count": self.review_request_count,
            "validation_ref_count": self.validation_ref_count,
            "specialist_refs": list(self.specialist_refs),
            "for_passive_supervision": True,
            "for_vispy_later": True,
            "publish_to_github": False,
        }


@dataclass(frozen=True, slots=True)
class FinalArtifactEnvelope:
    """Final artifact envelope for a later GitHub/local exchange adapter."""

    final_ref: str
    target_ref: str
    artifact_ref: str
    synthesis_ref: str
    title: str
    body: str
    evidence_refs: tuple[str, ...]
    context_influence_refs: tuple[str, ...] = ()
    validation_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_typed_ref("final_ref", self.final_ref, required_prefixes=("artifact-final:",))
        _require_typed_ref("target_ref", self.target_ref, required_prefixes=_ALLOWED_FINAL_TARGET_PREFIXES)
        _require_typed_ref("artifact_ref", self.artifact_ref, required_prefixes=_ALLOWED_ARTIFACT_PREFIXES)
        _require_typed_ref("synthesis_ref", self.synthesis_ref, required_prefixes=("synthesis:",))
        _require_non_empty("title", self.title)
        _require_non_empty("body", self.body)
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs("evidence_refs", self.evidence_refs, required_prefixes=_ALLOWED_CONTEXT_PREFIXES),
        )
        object.__setattr__(
            self,
            "context_influence_refs",
            _normalize_refs("context_influence_refs", self.context_influence_refs, allow_empty=True, required_prefixes=("ctx-result:", "ctx:", "sql:")),
        )
        object.__setattr__(
            self,
            "validation_refs",
            _normalize_refs("validation_refs", self.validation_refs, allow_empty=True, required_prefixes=_ALLOWED_VALIDATION_PREFIXES),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _FINAL_ARTIFACT_SCHEMA,
            "final_ref": self.final_ref,
            "target_ref": self.target_ref,
            "artifact_ref": self.artifact_ref,
            "synthesis_ref": self.synthesis_ref,
            "title": self.title,
            "body": self.body,
            "evidence_refs": list(self.evidence_refs),
            "context_influence_refs": list(self.context_influence_refs),
            "validation_refs": list(self.validation_refs),
            "github_exchange_role": "final artifact out only",
            "contains_internal_bus_statistics": False,
        }


def build_server_orientation_from_github_artifact(
    *,
    artifact: GitHubProjectArtifact,
    source_candidate: GitHubSourceCandidate,
    intent: str,
    requested_specialist_refs: tuple[str, ...],
    requested_document_kinds: tuple[str, ...],
    do_directives: tuple[str, ...] = (),
    avoid_directives: tuple[str, ...] = (),
    context_refs: tuple[str, ...] = (),
    policy: DeliberationPolicy | None = None,
) -> ServerOrientation:
    """Build the local server orientation from a fetched GitHub artifact."""

    if source_candidate.artifact.artifact_ref != artifact.artifact_ref:
        raise ValueError("source_candidate must originate from artifact")
    effective = policy or DeliberationPolicy()
    specialists = _limit_tuple(
        _normalize_refs("requested_specialist_refs", requested_specialist_refs, required_prefixes=_ALLOWED_SPECIALIST_PREFIXES),
        effective.max_specialists,
    )
    document_kinds = _limit_tuple(_normalize_texts("requested_document_kinds", requested_document_kinds), effective.max_document_kinds)
    do_limited = _limit_tuple(_normalize_texts("do_directives", do_directives, allow_empty=True), effective.max_directives)
    avoid_limited = _limit_tuple(_normalize_texts("avoid_directives", avoid_directives, allow_empty=True), effective.max_directives)
    context = _normalize_refs("context_refs", context_refs, allow_empty=True, required_prefixes=_ALLOWED_CONTEXT_PREFIXES)
    identity = f"{artifact.artifact_ref}\0{source_candidate.sql_record.context_ref}\0{intent}\0{'|'.join(specialists)}"
    return ServerOrientation(
        orientation_ref=f"orientation:server:{_digest(identity)}",
        artifact_ref=artifact.artifact_ref,
        source_ref=source_candidate.source_ref,
        sql_context_ref=source_candidate.sql_record.context_ref,
        title=f"Orientation serveur — {artifact.title}",
        intent=intent,
        requested_specialist_refs=specialists,
        requested_document_kinds=document_kinds,
        do_directives=do_limited,
        avoid_directives=avoid_limited,
        context_refs=context,
        metadata=(("source_system", "github_artifact_exchange"), ("publication", "final_only")),
    )


def build_specialist_preliminary_opinion(
    *,
    orientation: ServerOrientation,
    specialist_ref: str,
    stance: str,
    summary: str,
    recommendation: str,
    evidence_refs: tuple[str, ...] = (),
    requested_context_refs: tuple[str, ...] = (),
    proposed_specialist_refs: tuple[str, ...] = (),
    proposed_document_kinds: tuple[str, ...] = (),
    context_delta_refs: tuple[str, ...] = (),
    review_request_refs: tuple[str, ...] = (),
    validation_refs: tuple[str, ...] = (),
    bus_observation_refs: tuple[str, ...] = (),
    confidence: float = 0.0,
) -> SpecialistPreliminaryOpinion:
    """Build a preliminary specialist opinion before production starts."""

    identity = f"{orientation.orientation_ref}\0{specialist_ref}\0{stance}\0{summary}\0{recommendation}"
    return SpecialistPreliminaryOpinion(
        opinion_ref=f"specialist-opinion:{_digest(identity)}",
        orientation_ref=orientation.orientation_ref,
        specialist_ref=specialist_ref,
        stance=stance,
        summary=summary,
        recommendation=recommendation,
        evidence_refs=evidence_refs,
        requested_context_refs=requested_context_refs,
        proposed_specialist_refs=proposed_specialist_refs,
        proposed_document_kinds=proposed_document_kinds,
        context_delta_refs=context_delta_refs,
        review_request_refs=review_request_refs,
        validation_refs=validation_refs,
        bus_observation_refs=bus_observation_refs,
        confidence=confidence,
    )


def build_refined_demands_from_opinions(
    *,
    orientation: ServerOrientation,
    opinions: tuple[SpecialistPreliminaryOpinion, ...],
    round_index: int,
    policy: DeliberationPolicy | None = None,
) -> tuple[RefinedSpecialistDemand, ...]:
    """Recompose preliminary opinions into more precise specialist demands."""

    effective = policy or DeliberationPolicy()
    selected = tuple(opinion for opinion in opinions if opinion.orientation_ref == orientation.orientation_ref)[: effective.max_opinions_per_round]
    demands: list[RefinedSpecialistDemand] = []
    for opinion in selected:
        target_refs = opinion.proposed_specialist_refs or (opinion.specialist_ref,)
        output_kinds = opinion.proposed_document_kinds or orientation.requested_document_kinds
        depth = _depth_for_stance(opinion.stance)
        for target_ref in target_refs:
            for output_kind in output_kinds[:1]:
                identity = f"{orientation.orientation_ref}\0{opinion.opinion_ref}\0{target_ref}\0{output_kind}\0{round_index}"
                demands.append(
                    RefinedSpecialistDemand(
                        demand_ref=f"specialist-demand:{_digest(identity)}",
                        orientation_ref=orientation.orientation_ref,
                        source_opinion_refs=(opinion.opinion_ref,),
                        target_specialist_ref=target_ref,
                        title=f"Demande raffinée — {output_kind}",
                        prompt=_refined_prompt(orientation, opinion, output_kind),
                        requested_output_kind=output_kind,
                        depth=depth,
                        input_refs=(orientation.sql_context_ref, *orientation.context_refs, *opinion.evidence_refs),
                        context_refs=opinion.requested_context_refs,
                        review_request_refs=opinion.review_request_refs,
                        validation_refs=opinion.validation_refs,
                    )
                )
                if len(demands) >= effective.max_refined_demands:
                    return tuple(demands)
    return tuple(demands)


def build_deliberation_round(
    *,
    orientation: ServerOrientation,
    opinions: tuple[SpecialistPreliminaryOpinion, ...],
    refined_demands: tuple[RefinedSpecialistDemand, ...],
    round_index: int,
) -> DeliberationRound:
    """Build one local server/specialist deliberation round."""

    bus_refs = _unique_refs(ref for opinion in opinions for ref in opinion.bus_observation_refs)
    convergence = _infer_convergence(opinions, refined_demands)
    needs_next = convergence in {"needs_more_opinions", "needs_refinement", "ready_for_production"}
    identity = f"{orientation.orientation_ref}\0{round_index}\0{'|'.join(opinion.opinion_ref for opinion in opinions)}\0{'|'.join(demand.demand_ref for demand in refined_demands)}"
    return DeliberationRound(
        round_ref=f"deliberation-round:{_digest(identity)}",
        round_index=round_index,
        orientation=orientation,
        opinions=opinions,
        refined_demands=refined_demands,
        convergence_state=convergence,
        bus_observation_refs=bus_refs,
        needs_next_round=needs_next,
    )


def build_bus_statistics_from_rounds(rounds: tuple[DeliberationRound, ...]) -> SpecialistBusStatistics:
    """Aggregate local observation counts for passive supervision and VisPy."""

    if not rounds:
        raise ValueError("rounds must not be empty")
    round_refs = tuple(round_.round_ref for round_ in rounds)
    opinions = tuple(opinion for round_ in rounds for opinion in round_.opinions)
    demands = tuple(demand for round_ in rounds for demand in round_.refined_demands)
    bus_refs = _unique_refs(ref for round_ in rounds for ref in round_.bus_observation_refs)
    requested_context_count = sum(len(opinion.requested_context_refs) for opinion in opinions) + sum(len(demand.context_refs) for demand in demands)
    review_request_count = sum(len(opinion.review_request_refs) for opinion in opinions) + sum(len(demand.review_request_refs) for demand in demands)
    validation_ref_count = sum(len(opinion.validation_refs) for opinion in opinions) + sum(len(demand.validation_refs) for demand in demands)
    specialist_refs = _unique_refs(ref for opinion in opinions for ref in (opinion.specialist_ref, *opinion.proposed_specialist_refs))
    identity = f"{'|'.join(round_refs)}\0{len(opinions)}\0{len(demands)}\0{len(bus_refs)}"
    return SpecialistBusStatistics(
        stats_ref=f"bus-stats:specialist-deliberation:{_digest(identity)}",
        round_refs=round_refs,
        opinion_count=len(opinions),
        refined_demand_count=len(demands),
        bus_observation_count=len(bus_refs),
        requested_context_count=requested_context_count,
        review_request_count=review_request_count,
        validation_ref_count=validation_ref_count,
        specialist_refs=specialist_refs,
    )


def build_final_artifact_envelope(
    *,
    artifact: GitHubProjectArtifact,
    synthesis: SpecialistLiaisonSynthesis,
    target_ref: str,
    policy: DeliberationPolicy | None = None,
) -> FinalArtifactEnvelope:
    """Prepare a final exchange artifact only after local synthesis is ready."""

    if not synthesis.final_publication_ready:
        raise ValueError("synthesis must be final_publication_ready before final artifact exchange")
    effective = policy or DeliberationPolicy()
    body, _ = _truncate(_body_from_synthesis(synthesis), effective.max_final_body_chars)
    evidence_refs = _unique_refs(ref for section in synthesis.sections for ref in section.evidence_refs)
    identity = f"{artifact.artifact_ref}\0{synthesis.synthesis_ref}\0{target_ref}\0{body}"
    return FinalArtifactEnvelope(
        final_ref=f"artifact-final:{_digest(identity)}",
        target_ref=target_ref,
        artifact_ref=artifact.artifact_ref,
        synthesis_ref=synthesis.synthesis_ref,
        title=synthesis.title,
        body=body,
        evidence_refs=evidence_refs,
        context_influence_refs=synthesis.context_influence_refs,
        validation_refs=synthesis.validation_refs,
    )


def _infer_convergence(
    opinions: tuple[SpecialistPreliminaryOpinion, ...],
    refined_demands: tuple[RefinedSpecialistDemand, ...],
) -> str:
    if not opinions:
        return "needs_more_opinions"
    if all(opinion.stance == "impossible" for opinion in opinions):
        return "blocked"
    refinement_stances = {"risky", "better_alternative", "needs_context", "needs_specialist", "analysis_signal"}
    if any(opinion.stance in refinement_stances for opinion in opinions):
        return "needs_refinement"
    if refined_demands:
        return "ready_for_production"
    return "ready_for_final_synthesis"


def _depth_for_stance(stance: str) -> str:
    if stance in {"risky", "analysis_signal"}:
        return "audit"
    if stance in {"needs_context", "needs_specialist", "better_alternative"}:
        return "deep"
    return "standard"


def _refined_prompt(orientation: ServerOrientation, opinion: SpecialistPreliminaryOpinion, output_kind: str) -> str:
    parts = [
        f"Orientation serveur: {orientation.intent}",
        f"Avis préliminaire ({opinion.stance}): {opinion.summary}",
        f"Recommandation: {opinion.recommendation}",
        f"Livrable demandé: {output_kind}",
    ]
    if orientation.do_directives:
        parts.append("À faire: " + "; ".join(orientation.do_directives))
    if orientation.avoid_directives:
        parts.append("À éviter: " + "; ".join(orientation.avoid_directives))
    return "\n".join(parts)


def _body_from_synthesis(synthesis: SpecialistLiaisonSynthesis) -> str:
    lines = [synthesis.title, ""]
    for index, section in enumerate(synthesis.sections, start=1):
        lines.extend((f"{index}. {section.title}", section.body, ""))
    if synthesis.context_influence_refs:
        lines.append("Influences contexte validées: " + ", ".join(synthesis.context_influence_refs))
    if synthesis.validation_refs:
        lines.append("Validations: " + ", ".join(synthesis.validation_refs))
    return "\n".join(lines).strip()


def _truncate(value: str, max_chars: int) -> tuple[str, bool]:
    if len(value) <= max_chars:
        return value, False
    if max_chars <= 1:
        return value[:max_chars], True
    return value[: max_chars - 1].rstrip() + "…", True


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")


def _require_typed_ref(name: str, value: str, *, required_prefixes: tuple[str, ...] | None = None) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.match(value):
        raise ValueError(f"{name} must be a typed reference")
    if required_prefixes is not None and not value.startswith(required_prefixes):
        raise ValueError(f"{name} must start with one of: {', '.join(required_prefixes)}")


def _normalize_refs(
    name: str,
    refs: tuple[str, ...],
    *,
    allow_empty: bool = False,
    required_prefixes: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    values = tuple(refs)
    if not values and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    for ref in values:
        _require_typed_ref(name, ref, required_prefixes=required_prefixes)
    return _unique_refs(values)


def _normalize_texts(name: str, values: tuple[str, ...], *, allow_empty: bool = False) -> tuple[str, ...]:
    normalized = tuple(value.strip() for value in values if isinstance(value, str) and value.strip())
    if not normalized and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    return tuple(dict.fromkeys(normalized))


def _normalize_metadata(values: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    for key, value in values:
        _require_non_empty("metadata key", key)
        _require_non_empty("metadata value", value)
        normalized.append((key.strip(), value.strip()))
    return tuple(dict(normalized).items())


def _unique_refs(values) -> tuple[str, ...]:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return tuple(unique)


def _limit_tuple(values: tuple[str, ...], limit: int) -> tuple[str, ...]:
    return values[:limit]


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
