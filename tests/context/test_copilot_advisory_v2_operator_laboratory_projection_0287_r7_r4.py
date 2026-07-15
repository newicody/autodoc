from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import pytest

import context.github_operator_laboratory_advisory_projection_0281 as subject
from context.github_dual_artifact_laboratory_smoke_0275 import (
    GitHubDualArtifactLaboratorySmokeCommand,
)


@dataclass(frozen=True, slots=True)
class Decision:
    action: str = "promote"
    reason: str = "operator approved"

    def to_json_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "reason": self.reason,
            "resulting_status": "promoted",
        }


@dataclass(frozen=True, slots=True)
class Orientation:
    context_refs: tuple[str, ...] = ("sql:context:1",)
    do_directives: tuple[str, ...] = ()
    avoid_directives: tuple[str, ...] = ()
    metadata: tuple[tuple[str, str], ...] = ()

    def to_mapping(self) -> dict[str, Any]:
        return {
            "context_refs": list(self.context_refs),
            "do_directives": list(self.do_directives),
            "avoid_directives": list(self.avoid_directives),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class Deliberation:
    orientation: Orientation = Orientation()
    source_candidate_ref: str = "source-candidate:old"
    context_generation: int = 0

    def to_mapping(self) -> dict[str, Any]:
        return {
            "orientation": self.orientation.to_mapping(),
            "source_candidate_ref": self.source_candidate_ref,
            "context_generation": self.context_generation,
        }


@dataclass(frozen=True, slots=True)
class Laboratory:
    deliberation: Deliberation = Deliberation()

    def to_mapping(self) -> dict[str, Any]:
        return {"deliberation": self.deliberation.to_mapping()}


@dataclass(frozen=True, slots=True)
class IntakeResult:
    valid: bool
    issues: tuple[str, ...]
    mapping: dict[str, Any]

    def to_mapping(self) -> dict[str, Any]:
        return self.mapping


@dataclass(frozen=True, slots=True)
class LaboratoryResult:
    valid: bool = True
    issues: tuple[str, ...] = ()
    mapping: dict[str, Any] = field(
        default_factory=lambda: {
            "valid": True,
            "github_mutation_performed": False,
            "scheduler_created": False,
            "parallel_orchestrator_created": False,
            "publication_preview": {
                "source_sql_ref": "sql:lab:1",
                "source_final_ref": "artifact-final:lab:1",
            },
        }
    )

    def to_mapping(self) -> dict[str, Any]:
        return self.mapping


def _v2_intake_mapping() -> dict[str, Any]:
    return {
        "schema": "missipy.github.dual_artifact_source_candidate_intake.v1",
        "valid": True,
        "issues": [],
        "request": {
            "artifact_ref": "github-request:newicody/projects:15:def",
        },
        "advisory": {
            "schema": "missipy.github.copilot_advisory.v2",
            "origin_frame_id": "github-frame:newicody/projects:15:42",
            "ticket_revision_id": "github-ticket-revision:abc",
            "artifact_ref": "github-advisory:abc",
            "request_artifact_ref": (
                "github-request:newicody/projects:15:def"
            ),
            "response_digest": "a" * 64,
            "concrete_objective": "Déterminer l’objectif concret.",
            "expected_result": "Produire un premier avis vérifiable.",
            "provided_constraints": [
                "Ne pas créer de nouveau Scheduler.",
            ],
            "success_criteria": [
                "La preview conserve exactement les quatre champs v2.",
            ],
            "producer_kind": "github_copilot_cli",
            "trusted": False,
            "usable_as_hint": True,
            "usable_as_authority": False,
        },
        "manifest": {},
        "source_candidate": {
            "candidate_id": "github-request-0123456789abcdef",
            "title": "Research",
        },
        "request_authoritative": True,
        "advisory_used_as_hint_only": True,
    }


def _v1_intake_mapping() -> dict[str, Any]:
    mapping = _v2_intake_mapping()
    mapping["advisory"] = {
        "schema": "missipy.github.copilot_advisory.v1",
        "origin_frame_id": "github-frame:newicody/projects:15:42",
        "ticket_revision_id": "github-ticket-revision:abc",
        "artifact_ref": "github-advisory:legacy",
        "request_artifact_ref": "github-request:newicody/projects:15:def",
        "response_digest": "b" * 64,
        "summary": "Legacy summary",
        "suggested_route": "Legacy route",
        "assumptions": [],
        "questions": ["Legacy question"],
        "risks": ["Legacy risk"],
        "confidence": 0.5,
        "producer_kind": "github_copilot_cli",
        "trusted": False,
        "usable_as_hint": True,
        "usable_as_authority": False,
    }
    return mapping


def _command() -> subject.GitHubOperatorLaboratoryAdvisoryProjectionCommand:
    smoke = GitHubDualArtifactLaboratorySmokeCommand(
        decision=Decision(),
        laboratory=Laboratory(),
        policy_decision_id="policy:test:0287-r7-r4",
    )
    return subject.GitHubOperatorLaboratoryAdvisoryProjectionCommand(
        smoke=smoke,
    )


def test_v1_projection_and_preview_keep_historical_shape() -> None:
    intake = _v1_intake_mapping()
    projection = subject.build_copilot_advisory_laboratory_projection(intake)
    mapping = projection.to_mapping()
    preview = subject._publication_preview(
        intake_mapping=intake,
        projection=projection,
        laboratory_mapping=LaboratoryResult().to_mapping(),
    )

    assert isinstance(
        projection,
        subject.GitHubCopilotAdvisoryLaboratoryProjection,
    )
    assert mapping["schema"] == subject.PROJECTION_SCHEMA_V1
    assert mapping["summary"] == "Legacy summary"
    assert preview["schema"] == subject.PUBLICATION_PREVIEW_SCHEMA_V1
    assert preview["suggested_route"] == "Legacy route"
    assert "concrete_objective" not in mapping
    assert "concrete_objective" not in preview


def test_v2_projection_keeps_only_first_opinion_semantics() -> None:
    projection = subject.build_copilot_advisory_laboratory_projection(
        _v2_intake_mapping()
    )
    mapping = projection.to_mapping()

    assert isinstance(
        projection,
        subject.GitHubCopilotFirstOpinionLaboratoryProjection,
    )
    assert mapping["schema"] == subject.PROJECTION_SCHEMA_V2
    assert mapping["concrete_objective"].startswith("Déterminer")
    assert mapping["success_criteria"] == [
        "La preview conserve exactement les quatre champs v2."
    ]
    for legacy in (
        "summary",
        "suggested_route",
        "assumptions",
        "questions",
        "risks",
        "confidence",
    ):
        assert legacy not in mapping
    assert mapping["usable_as_authority"] is False


def test_v2_publication_preview_is_versioned_and_not_v1_shaped() -> None:
    intake = _v2_intake_mapping()
    projection = subject.build_copilot_advisory_laboratory_projection(intake)

    preview = subject._publication_preview(
        intake_mapping=intake,
        projection=projection,
        laboratory_mapping=LaboratoryResult().to_mapping(),
    )

    assert preview["schema"] == subject.PUBLICATION_PREVIEW_SCHEMA_V2
    assert preview["expected_result"].startswith("Produire")
    assert preview["provided_constraints"] == [
        "Ne pas créer de nouveau Scheduler."
    ]
    assert preview["operator_decision_required"] is True
    assert preview["remote_mutation_allowed"] is False
    assert "summary" not in preview
    assert "suggested_route" not in preview


def test_v2_projection_rejects_invalid_success_criteria_type() -> None:
    intake = _v2_intake_mapping()
    intake["advisory"]["success_criteria"] = "not-an-array"

    with pytest.raises(ValueError, match="must be an array"):
        subject.build_copilot_advisory_laboratory_projection(intake)


def test_v2_runs_through_existing_operator_laboratory_composition(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_intake(*args, **kwargs):
        return IntakeResult(True, (), _v2_intake_mapping())

    async def fake_laboratory(*args, **kwargs):
        captured["command"] = args[4]
        return LaboratoryResult()

    monkeypatch.setattr(
        subject,
        "run_github_dual_artifact_source_candidate_intake",
        fake_intake,
    )
    monkeypatch.setattr(
        subject,
        "run_github_dual_artifact_laboratory_smoke",
        fake_laboratory,
    )

    result = asyncio.run(
        subject.run_github_operator_laboratory_advisory_projection(
            object(),
            b"request",
            b"manifest",
            b"advisory",
            _command(),
            store=object(),
        )
    )

    assert result.valid is True
    assert result.publication_preview["schema"] == (
        subject.PUBLICATION_PREVIEW_SCHEMA_V2
    )
    assert result.advisory_projection["schema"] == (
        subject.PROJECTION_SCHEMA_V2
    )
    effective = captured["command"].laboratory.deliberation
    metadata = dict(effective.orientation.metadata)
    assert metadata["copilot_advisory_projection_schema"] == (
        subject.PROJECTION_SCHEMA_V2
    )
    assert effective.context_generation == 1
    assert result.scheduler_created is False
    assert result.github_mutation_performed is False
