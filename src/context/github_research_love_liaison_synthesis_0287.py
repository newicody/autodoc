"""Build a distinct liaison synthesis from the two SQL-rehydrated analyses.

r16-r14 recalls exactly the two SQL authority objects and keeps their bodies in
memory.  This unit validates those immutable bodies, recognizes the two love
analysis schemas, mutualizes convergence/contradiction/uncertainty evidence,
normalizes three existing SpecialistOutputFragment values and delegates the
actual liaison surface to ``build_specialist_liaison_synthesis``.

The two source analyses remain immutable and independently addressable.  This
unit creates no final publication packet, SQL/Qdrant write, inference call,
Scheduler, laboratory visit, specialist execution or GitHub mutation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
from types import MappingProxyType
from typing import Any

from context.github_research_love_two_analysis_recall_0287 import (
    GitHubResearchLoveTwoAnalysisRecallResult,
)
from context.love_memory_evidence_liaison_synthesis_0287 import (
    LOVE_EVIDENCE_MUTUALIZATION_SCHEMA,
    LoveEvidenceMutualization,
)
from context.love_study_contracts_0287 import (
    LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA,
    LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    LOVE_RELATIONAL_DYNAMICS_ANALYSIS_SCHEMA,
    LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
)
from context.specialist_liaison_synthesis import (
    SpecialistLiaisonPolicy,
    SpecialistLiaisonSynthesis,
    SpecialistOutputFragment,
    build_specialist_liaison_synthesis,
)

PLAN_SCHEMA = "missipy.github.research_love_liaison_synthesis_plan.v1"
RESULT_SCHEMA = "missipy.github.research_love_liaison_synthesis_result.v1"
_VISIT_RESULT_SCHEMA = "missipy.laboratory.visit_result.v1"
_ALLOWED_FRAGMENT_EVIDENCE_PREFIXES = (
    "sql:",
    "qdrant:",
    "ctx:",
    "ctx-fragment:",
    "artifact:",
)


class GitHubResearchLoveLiaisonSynthesisError(RuntimeError):
    """Raised when the two-source liaison boundary is incoherent."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveLiaisonSynthesisCommand:
    """In-memory liaison request from one successful r16-r14 recall."""

    recall: GitHubResearchLoveTwoAnalysisRecallResult
    title: str = "Synthèse de liaison de l’étude"
    max_section_chars: int = 8_192

    def __post_init__(self) -> None:
        if not isinstance(
            self.recall,
            GitHubResearchLoveTwoAnalysisRecallResult,
        ):
            raise TypeError(
                "recall must be GitHubResearchLoveTwoAnalysisRecallResult"
            )
        title = self.title.strip()
        if not title:
            raise GitHubResearchLoveLiaisonSynthesisError(
                "title must not be empty"
            )
        object.__setattr__(self, "title", title)
        if (
            isinstance(self.max_section_chars, bool)
            or not isinstance(self.max_section_chars, int)
            or self.max_section_chars <= 0
        ):
            raise GitHubResearchLoveLiaisonSynthesisError(
                "max_section_chars must be a positive integer"
            )


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveLiaisonSynthesisPlan:
    """Validated two-analysis identity and deterministic synthesis inputs."""

    schema: str
    work_package_ref: str
    recall_plan_digest: str
    first_sql_ref: str
    second_sql_ref: str
    first_analysis_ref: str
    second_analysis_ref: str
    study_ref: str
    title: str
    plan_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema != PLAN_SCHEMA:
            raise GitHubResearchLoveLiaisonSynthesisError(
                "unsupported liaison synthesis plan schema"
            )
        if not self.work_package_ref.startswith("research-work-package:"):
            raise GitHubResearchLoveLiaisonSynthesisError(
                "work_package_ref must start with research-work-package:"
            )
        if not self.recall_plan_digest.startswith("sha256:"):
            raise GitHubResearchLoveLiaisonSynthesisError(
                "recall_plan_digest must be sha256:*"
            )
        if self.first_sql_ref == self.second_sql_ref:
            raise GitHubResearchLoveLiaisonSynthesisError(
                "source SQL objects must remain distinct"
            )
        if not self.first_analysis_ref.startswith("love-analysis:"):
            raise GitHubResearchLoveLiaisonSynthesisError(
                "first_analysis_ref must be typed"
            )
        if not self.second_analysis_ref.startswith("love-analysis:"):
            raise GitHubResearchLoveLiaisonSynthesisError(
                "second_analysis_ref must be typed"
            )
        if self.first_analysis_ref == self.second_analysis_ref:
            raise GitHubResearchLoveLiaisonSynthesisError(
                "source analyses must remain distinct"
            )
        if not self.study_ref.startswith("love-study:"):
            raise GitHubResearchLoveLiaisonSynthesisError(
                "study_ref must start with love-study:"
            )
        if not self.title.strip():
            raise GitHubResearchLoveLiaisonSynthesisError(
                "title must not be empty"
            )
        object.__setattr__(self, "plan_digest", _plan_digest(self))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "plan_digest": self.plan_digest,
            "work_package_ref": self.work_package_ref,
            "recall_plan_digest": self.recall_plan_digest,
            "first_sql_ref": self.first_sql_ref,
            "second_sql_ref": self.second_sql_ref,
            "first_analysis_ref": self.first_analysis_ref,
            "second_analysis_ref": self.second_analysis_ref,
            "study_ref": self.study_ref,
            "title": self.title,
            "boundaries": {
                "two_source_analyses_remain_distinct": True,
                "source_authority_objects_immutable": True,
                "existing_liaison_synthesis_reused": True,
                "source_authority_bodies_serialized": False,
                "final_publication_packet_created": False,
                "sql_write_performed": False,
                "qdrant_write_performed": False,
                "inference_performed": False,
                "github_mutation_performed": False,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveLiaisonSynthesisResult:
    """A local liaison synthesis, deliberately not publication-ready."""

    schema: str
    valid: bool
    status: str
    issues: tuple[str, ...]
    plan: GitHubResearchLoveLiaisonSynthesisPlan
    mutualization: LoveEvidenceMutualization | None = None
    fragments: tuple[SpecialistOutputFragment, ...] = ()
    synthesis: SpecialistLiaisonSynthesis | None = None

    def __post_init__(self) -> None:
        if self.schema != RESULT_SCHEMA:
            raise GitHubResearchLoveLiaisonSynthesisError(
                "unsupported liaison synthesis result schema"
            )
        object.__setattr__(self, "fragments", tuple(self.fragments))
        if self.valid:
            if self.status != "synthesized":
                raise GitHubResearchLoveLiaisonSynthesisError(
                    "valid liaison status must be synthesized"
                )
            if self.mutualization is None:
                raise GitHubResearchLoveLiaisonSynthesisError(
                    "valid liaison requires evidence mutualization"
                )
            if len(self.fragments) != 3:
                raise GitHubResearchLoveLiaisonSynthesisError(
                    "valid liaison requires two analyses and one audit fragment"
                )
            if self.synthesis is None:
                raise GitHubResearchLoveLiaisonSynthesisError(
                    "valid liaison requires SpecialistLiaisonSynthesis"
                )
            if self.synthesis.final_publication_ready:
                raise GitHubResearchLoveLiaisonSynthesisError(
                    "r16-r15 must not mark the synthesis publication-ready"
                )
            if not self.synthesis.provenance_hidden:
                raise GitHubResearchLoveLiaisonSynthesisError(
                    "end-user liaison must hide specialist provenance"
                )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "status": self.status,
            "issues": list(self.issues),
            "plan": self.plan.to_mapping(),
            "mutualization": (
                self.mutualization.to_mapping()
                if self.mutualization is not None
                else None
            ),
            "fragment_refs": [
                fragment.fragment_ref for fragment in self.fragments
            ],
            "synthesis": (
                self.synthesis.to_mapping()
                if self.synthesis is not None
                else None
            ),
            "boundaries": {
                "source_analysis_count": 2,
                "source_authority_objects_modified": False,
                "source_authority_bodies_serialized": False,
                "specialist_provenance_hidden_from_end_user": bool(
                    self.synthesis and self.synthesis.provenance_hidden
                ),
                "final_publication_ready": bool(
                    self.synthesis
                    and self.synthesis.final_publication_ready
                ),
                "final_publication_packet_created": False,
                "sql_write_performed": False,
                "qdrant_write_performed": False,
                "openvino_inference_performed": False,
                "scheduler_created": False,
                "laboratory_execution_started": False,
                "specialist_execution_started": False,
                "github_mutation_performed": False,
            },
        }


def build_github_research_love_liaison_synthesis(
    command: GitHubResearchLoveLiaisonSynthesisCommand,
) -> GitHubResearchLoveLiaisonSynthesisResult:
    """Validate, mutualize and normalize the two recalled SQL analyses."""

    recall = command.recall
    try:
        if not recall.valid or recall.status != "recalled":
            raise GitHubResearchLoveLiaisonSynthesisError(
                "two-analysis recall must be valid and recalled"
            )
        first_item = recall.first_item
        second_item = recall.second_item
        _verify_rehydrated_item(first_item)
        _verify_rehydrated_item(second_item)

        decoded = (
            _decode_visit_result(first_item.body),
            _decode_visit_result(second_item.body),
        )
        first_result, first_analysis = _select_analysis(
            decoded,
            expected_schema=LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA,
        )
        second_result, second_analysis = _select_analysis(
            decoded,
            expected_schema=LOVE_RELATIONAL_DYNAMICS_ANALYSIS_SCHEMA,
        )
        _validate_analysis_pair(first_analysis, second_analysis)

        item_by_analysis_schema = {
            _required_mapping(
                _decode_visit_result(first_item.body),
                "machine_result",
            )["schema"]: first_item,
            _required_mapping(
                _decode_visit_result(second_item.body),
                "machine_result",
            )["schema"]: second_item,
        }
        first_source = item_by_analysis_schema[
            LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA
        ]
        second_source = item_by_analysis_schema[
            LOVE_RELATIONAL_DYNAMICS_ANALYSIS_SCHEMA
        ]
        plan = GitHubResearchLoveLiaisonSynthesisPlan(
            schema=PLAN_SCHEMA,
            work_package_ref=recall.plan.work_package_ref,
            recall_plan_digest=recall.plan.plan_digest,
            first_sql_ref=first_source.sql_ref,
            second_sql_ref=second_source.sql_ref,
            first_analysis_ref=_required_text(
                first_analysis,
                "analysis_ref",
            ),
            second_analysis_ref=_required_text(
                second_analysis,
                "analysis_ref",
            ),
            study_ref=_required_text(first_analysis, "study_ref"),
            title=command.title,
        )
        mutualization = _mutualize(
            first_analysis,
            second_analysis,
        )
        fragments = _build_fragments(
            plan=plan,
            first_result=first_result,
            first_analysis=first_analysis,
            first_source=first_source,
            second_result=second_result,
            second_analysis=second_analysis,
            second_source=second_source,
            mutualization=mutualization,
        )
        synthesis = build_specialist_liaison_synthesis(
            request_ref=plan.work_package_ref,
            title=plan.title,
            fragments=fragments,
            policy=SpecialistLiaisonPolicy(
                max_fragments=3,
                max_section_chars=command.max_section_chars,
                hide_specialist_provenance_from_user=True,
                include_review_requests=True,
                include_context_influence=True,
            ),
        )
        return GitHubResearchLoveLiaisonSynthesisResult(
            schema=RESULT_SCHEMA,
            valid=True,
            status="synthesized",
            issues=(),
            plan=plan,
            mutualization=mutualization,
            fragments=fragments,
            synthesis=synthesis,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        return GitHubResearchLoveLiaisonSynthesisResult(
            schema=RESULT_SCHEMA,
            valid=False,
            status="failed",
            issues=(f"{type(exc).__name__}: {exc}",),
            plan=_invalid_plan(command),
        )


def _verify_rehydrated_item(item: Any) -> None:
    if item.authority_kind != "context_object":
        raise GitHubResearchLoveLiaisonSynthesisError(
            "recalled analysis must be a context authority object"
        )
    if not item.sql_ref.startswith("context-object:"):
        raise GitHubResearchLoveLiaisonSynthesisError(
            "recalled SQL reference must be context-object:*"
        )
    if not item.body:
        raise GitHubResearchLoveLiaisonSynthesisError(
            "recalled authority body must not be empty"
        )
    expected = "sha256:" + hashlib.sha256(
        item.body.encode("utf-8")
    ).hexdigest()
    if item.content_digest != expected:
        raise GitHubResearchLoveLiaisonSynthesisError(
            "rehydrated authority body digest mismatch"
        )


def _decode_visit_result(body: str) -> Mapping[str, Any]:
    try:
        value = json.loads(body)
    except json.JSONDecodeError as exc:
        raise GitHubResearchLoveLiaisonSynthesisError(
            f"authority body is not valid JSON: {exc}"
        ) from exc
    if not isinstance(value, Mapping):
        raise GitHubResearchLoveLiaisonSynthesisError(
            "authority body must contain a JSON object"
        )
    if value.get("schema") != _VISIT_RESULT_SCHEMA:
        raise GitHubResearchLoveLiaisonSynthesisError(
            "authority body is not a laboratory visit result"
        )
    if value.get("status") != "completed":
        raise GitHubResearchLoveLiaisonSynthesisError(
            "laboratory visit result must be completed"
        )
    _required_mapping(value, "machine_result")
    return value


def _select_analysis(
    decoded: Sequence[Mapping[str, Any]],
    *,
    expected_schema: str,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    matches: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for visit_result in decoded:
        machine = _required_mapping(visit_result, "machine_result")
        if machine.get("schema") == expected_schema:
            matches.append((visit_result, machine))
    if len(matches) != 1:
        raise GitHubResearchLoveLiaisonSynthesisError(
            f"expected exactly one analysis with schema {expected_schema}"
        )
    return matches[0]


def _validate_analysis_pair(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
) -> None:
    if first.get("specialist_ref") != LOVE_CONCEPT_AFFECT_SPECIALIST_REF:
        raise GitHubResearchLoveLiaisonSynthesisError(
            "unexpected first specialist"
        )
    if second.get("specialist_ref") != LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF:
        raise GitHubResearchLoveLiaisonSynthesisError(
            "unexpected second specialist"
        )
    first_ref = _required_text(first, "analysis_ref")
    second_ref = _required_text(second, "analysis_ref")
    if first_ref == second_ref:
        raise GitHubResearchLoveLiaisonSynthesisError(
            "analysis references must remain distinct"
        )
    study_ref = _required_text(first, "study_ref")
    if second.get("study_ref") != study_ref:
        raise GitHubResearchLoveLiaisonSynthesisError(
            "analysis study_ref mismatch"
        )
    if second.get("source_analysis_refs") != [first_ref]:
        raise GitHubResearchLoveLiaisonSynthesisError(
            "second analysis provenance must reference only the first analysis"
        )
    if first.get("context_revision_ref") != second.get(
        "context_revision_ref"
    ):
        raise GitHubResearchLoveLiaisonSynthesisError(
            "analysis context revision mismatch"
        )
    for name, analysis in (("first", first), ("second", second)):
        findings = analysis.get("findings")
        if not isinstance(findings, list) or not findings:
            raise GitHubResearchLoveLiaisonSynthesisError(
                f"{name} analysis findings must not be empty"
            )
        for finding in findings:
            if not isinstance(finding, Mapping):
                raise GitHubResearchLoveLiaisonSynthesisError(
                    f"{name} analysis findings must be objects"
                )
            _required_text(finding, "statement")
            if finding.get("status") not in {
                "observed",
                "inferred",
                "absent",
                "contradicted",
            }:
                raise GitHubResearchLoveLiaisonSynthesisError(
                    f"{name} analysis finding status is unsupported"
                )


def _mutualize(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
) -> LoveEvidenceMutualization:
    first_dimensions = set(_text_list(first.get("concepts"))) | set(
        _text_list(first.get("affects"))
    )
    second_dimensions = set(_text_list(second.get("dynamics")))
    first_ref = _required_text(first, "analysis_ref")
    second_ref = _required_text(second, "analysis_ref")
    digest = hashlib.sha256(
        f"{first_ref}\0{second_ref}".encode("utf-8")
    ).hexdigest()[:24]
    return LoveEvidenceMutualization(
        schema=LOVE_EVIDENCE_MUTUALIZATION_SCHEMA,
        mutualization_ref=f"love-evidence-mutualization:{digest}",
        study_ref=_required_text(first, "study_ref"),
        analysis_refs=(first_ref, second_ref),
        convergences=tuple(sorted(first_dimensions & second_dimensions)),
        contradictions=_unique_texts(
            _text_list(first.get("contradictions"))
            + _text_list(second.get("contradictions"))
        ),
        uncertainties=_unique_texts(
            _text_list(first.get("uncertainties"))
            + _text_list(second.get("uncertainties"))
        ),
        recommendations=_unique_texts(
            _text_list(first.get("recommendations"))
            + _text_list(second.get("recommendations"))
        ),
        evidence_refs=_unique_texts(
            _text_list(first.get("evidence_refs"))
            + _text_list(second.get("evidence_refs"))
        ),
    )


def _build_fragments(
    *,
    plan: GitHubResearchLoveLiaisonSynthesisPlan,
    first_result: Mapping[str, Any],
    first_analysis: Mapping[str, Any],
    first_source: Any,
    second_result: Mapping[str, Any],
    second_analysis: Mapping[str, Any],
    second_source: Any,
    mutualization: LoveEvidenceMutualization,
) -> tuple[SpecialistOutputFragment, ...]:
    first_sql_evidence = _sql_evidence_ref(first_source.sql_ref)
    second_sql_evidence = _sql_evidence_ref(second_source.sql_ref)
    first_fragment = SpecialistOutputFragment(
        fragment_ref=_fragment_ref(
            plan.plan_digest,
            "first",
            _required_text(first_analysis, "analysis_ref"),
        ),
        result_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        output_kind="domain_analysis",
        title="Concepts et affects",
        body=_analysis_body(
            first_analysis,
            fallback=_required_text(first_result, "human_representation"),
        ),
        evidence_refs=_fragment_evidence_refs(
            first_analysis,
            first_sql_evidence,
        ),
        context_delta_refs=(first_sql_evidence,),
        validation_refs=(),
        payload_ref=first_source.sql_ref,
        depth="deep",
        metadata=(
            ("analysis_ref", _required_text(first_analysis, "analysis_ref")),
            ("source_sql_ref", first_source.sql_ref),
            ("work_package_ref", plan.work_package_ref),
        ),
    )
    second_fragment = SpecialistOutputFragment(
        fragment_ref=_fragment_ref(
            plan.plan_digest,
            "second",
            _required_text(second_analysis, "analysis_ref"),
        ),
        result_ref=LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
        output_kind="domain_analysis",
        title="Dynamiques relationnelles",
        body=_analysis_body(
            second_analysis,
            fallback=_required_text(second_result, "human_representation"),
        ),
        evidence_refs=_fragment_evidence_refs(
            second_analysis,
            second_sql_evidence,
        ),
        context_delta_refs=(second_sql_evidence,),
        validation_refs=(),
        payload_ref=second_source.sql_ref,
        depth="deep",
        metadata=(
            ("analysis_ref", _required_text(second_analysis, "analysis_ref")),
            ("source_sql_ref", second_source.sql_ref),
            ("work_package_ref", plan.work_package_ref),
        ),
    )
    mutual_fragment = SpecialistOutputFragment(
        fragment_ref=_fragment_ref(
            plan.plan_digest,
            "mutualization",
            mutualization.mutualization_ref,
        ),
        result_ref="ctx-result:github-love-evidence-mutualization",
        output_kind="evidence_mutualization",
        title="Convergences, contradictions et limites",
        body=_mutualization_body(mutualization),
        evidence_refs=(first_sql_evidence, second_sql_evidence),
        context_delta_refs=(
            first_sql_evidence,
            second_sql_evidence,
        ),
        validation_refs=(),
        payload_ref=mutualization.mutualization_ref,
        depth="audit",
        metadata=(
            ("distinct_laboratory_count", "1"),
            ("distinct_specialist_count", "2"),
            ("multi_laboratory_pipeline_eligible", "false"),
        ),
    )
    return (first_fragment, second_fragment, mutual_fragment)


def _analysis_body(
    analysis: Mapping[str, Any],
    *,
    fallback: str,
) -> str:
    lines: list[str] = []
    local_synthesis = analysis.get("local_synthesis")
    if isinstance(local_synthesis, str) and local_synthesis.strip():
        lines.extend(("Synthèse locale :", local_synthesis.strip(), ""))
    lines.append("Constats :")
    for finding in analysis.get("findings", []):
        assert isinstance(finding, Mapping)
        statement = _required_text(finding, "statement")
        status = _required_text(finding, "status")
        confidence = finding.get("confidence")
        confidence_text = (
            f"{float(confidence):.2f}"
            if isinstance(confidence, (int, float))
            and not isinstance(confidence, bool)
            else "non précisée"
        )
        lines.append(
            f"- [{status}; confiance {confidence_text}] {statement}"
        )
    _append_section(lines, "Contradictions", analysis.get("contradictions"))
    _append_section(lines, "Incertitudes", analysis.get("uncertainties"))
    _append_section(lines, "Limites", analysis.get("limitations"))
    _append_section(lines, "Recommandations", analysis.get("recommendations"))
    body = "\n".join(lines).strip()
    return body or fallback


def _mutualization_body(value: LoveEvidenceMutualization) -> str:
    return "\n".join(
        (
            "Comparaison locale des deux analyses.",
            "",
            "Convergences :",
            *(
                tuple(f"- {item}" for item in value.convergences)
                or ("- Aucune convergence terminologique explicite.",)
            ),
            "",
            "Contradictions :",
            *(
                tuple(f"- {item}" for item in value.contradictions)
                or ("- Aucune contradiction explicite.",)
            ),
            "",
            "Incertitudes :",
            *(
                tuple(f"- {item}" for item in value.uncertainties)
                or ("- Aucune incertitude explicite.",)
            ),
            "",
            "Recommandations mutualisées :",
            *(
                tuple(f"- {item}" for item in value.recommendations)
                or ("- Aucune recommandation mutualisée explicite.",)
            ),
            "",
            (
                "Limite de validation : les deux spécialistes ont travaillé "
                "dans un seul laboratoire ; la validation multi-laboratoires "
                "reste différée."
            ),
        )
    )


def _fragment_evidence_refs(
    analysis: Mapping[str, Any],
    sql_ref: str,
) -> tuple[str, ...]:
    values = [sql_ref]
    values.extend(
        item
        for item in _text_list(analysis.get("evidence_refs"))
        if item.startswith(_ALLOWED_FRAGMENT_EVIDENCE_PREFIXES)
    )
    values.extend(
        item
        for item in _text_list(analysis.get("artifact_refs"))
        if item.startswith(_ALLOWED_FRAGMENT_EVIDENCE_PREFIXES)
    )
    return _unique_texts(values)


def _sql_evidence_ref(object_ref: str) -> str:
    if not object_ref.startswith("context-object:"):
        raise GitHubResearchLoveLiaisonSynthesisError(
            "SQL authority object reference must be context-object:*"
        )
    return f"sql:{object_ref}"


def _append_section(
    lines: list[str],
    title: str,
    raw_values: object,
) -> None:
    values = _text_list(raw_values)
    if not values:
        return
    lines.extend(("", f"{title} :"))
    lines.extend(f"- {item}" for item in values)


def _text_list(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise GitHubResearchLoveLiaisonSynthesisError(
            "analysis list field must be a list"
        )
    values: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise GitHubResearchLoveLiaisonSynthesisError(
                "analysis list entries must be non-empty strings"
            )
        values.append(item.strip())
    return values


def _unique_texts(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item.strip() for item in values if item.strip()))


def _fragment_ref(*parts: str) -> str:
    digest = hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"specialist-fragment:github-love-{digest}"


def _required_mapping(
    value: Mapping[str, Any],
    name: str,
) -> Mapping[str, Any]:
    candidate = value.get(name)
    if not isinstance(candidate, Mapping):
        raise GitHubResearchLoveLiaisonSynthesisError(
            f"{name} must be an object"
        )
    return candidate


def _required_text(
    value: Mapping[str, Any],
    name: str,
) -> str:
    candidate = value.get(name)
    if not isinstance(candidate, str) or not candidate.strip():
        raise GitHubResearchLoveLiaisonSynthesisError(
            f"{name} must not be empty"
        )
    return candidate.strip()


def _plan_digest(
    plan: GitHubResearchLoveLiaisonSynthesisPlan,
) -> str:
    payload = {
        "schema": plan.schema,
        "work_package_ref": plan.work_package_ref,
        "recall_plan_digest": plan.recall_plan_digest,
        "first_sql_ref": plan.first_sql_ref,
        "second_sql_ref": plan.second_sql_ref,
        "first_analysis_ref": plan.first_analysis_ref,
        "second_analysis_ref": plan.second_analysis_ref,
        "study_ref": plan.study_ref,
        "title": plan.title,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _invalid_plan(
    command: GitHubResearchLoveLiaisonSynthesisCommand,
) -> GitHubResearchLoveLiaisonSynthesisPlan:
    digest = hashlib.sha256(command.title.encode("utf-8")).hexdigest()
    return GitHubResearchLoveLiaisonSynthesisPlan(
        schema=PLAN_SCHEMA,
        work_package_ref="research-work-package:invalid",
        recall_plan_digest="sha256:" + "0" * 64,
        first_sql_ref="context-object:invalid-first",
        second_sql_ref="context-object:invalid-second",
        first_analysis_ref=f"love-analysis:invalid-first-{digest[:8]}",
        second_analysis_ref=f"love-analysis:invalid-second-{digest[:8]}",
        study_ref=f"love-study:invalid-{digest[:8]}",
        title=command.title,
    )


__all__ = (
    "GitHubResearchLoveLiaisonSynthesisCommand",
    "GitHubResearchLoveLiaisonSynthesisError",
    "GitHubResearchLoveLiaisonSynthesisPlan",
    "GitHubResearchLoveLiaisonSynthesisResult",
    "PLAN_SCHEMA",
    "RESULT_SCHEMA",
    "build_github_research_love_liaison_synthesis",
)
