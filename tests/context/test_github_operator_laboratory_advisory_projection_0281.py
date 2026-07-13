from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

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
    mapping: dict[str, Any] = field(default_factory=lambda: {
        "valid": True,
        "github_mutation_performed": False,
        "scheduler_created": False,
        "parallel_orchestrator_created": False,
        "publication_preview": {
            "source_sql_ref": "sql:lab:1",
            "source_final_ref": "artifact-final:lab:1",
        },
    })

    def to_mapping(self) -> dict[str, Any]:
        return self.mapping


def _intake_mapping(with_advisory: bool = True) -> dict[str, Any]:
    advisory = {
        "schema": "missipy.github.copilot_advisory.v1",
        "origin_frame_id": "github-frame:newicody/projects:15:42",
        "ticket_revision_id": "github-ticket-revision:abc",
        "artifact_ref": "github-advisory:abc",
        "request_artifact_ref": "github-request:newicody/projects:15:def",
        "response_digest": "a" * 64,
        "summary": "Comparer les contraintes avant de produire.",
        "suggested_route": "Demander un audit puis une synthèse.",
        "assumptions": ["Le ticket est complet."],
        "questions": ["Quel niveau de preuve est requis ?"],
        "risks": ["Contexte incomplet."],
        "confidence": 0.72,
        "producer_kind": "github_copilot_cli",
        "trusted": False,
        "usable_as_hint": True,
        "usable_as_authority": False,
    } if with_advisory else {}
    return {
        "schema": "missipy.github.dual_artifact_source_candidate_intake.v1",
        "valid": True,
        "issues": [],
        "request": {
            "artifact_ref": "github-request:newicody/projects:15:def",
        },
        "advisory": advisory,
        "manifest": {},
        "source_candidate": {
            "candidate_id": "github-request-0123456789abcdef",
            "title": "Research",
        },
        "request_authoritative": True,
        "advisory_used_as_hint_only": True,
    }


def _command() -> subject.GitHubOperatorLaboratoryAdvisoryProjectionCommand:
    smoke = GitHubDualArtifactLaboratorySmokeCommand(
        decision=Decision(),
        laboratory=Laboratory(),
        policy_decision_id="policy:test:0281-r5",
    )
    return subject.GitHubOperatorLaboratoryAdvisoryProjectionCommand(
        smoke=smoke,
    )


def test_projection_retains_full_advisory_and_locks_authority() -> None:
    projection = subject.build_copilot_advisory_laboratory_projection(
        _intake_mapping()
    )
    mapping = projection.to_mapping()

    assert mapping["context_ref"].startswith("ctx:github-advisory:")
    assert mapping["summary"] == "Comparer les contraintes avant de produire."
    assert mapping["questions"] == ["Quel niveau de preuve est requis ?"]
    assert mapping["risks"] == ["Contexte incomplet."]
    assert mapping["trusted"] is False
    assert mapping["usable_as_hint"] is True
    assert mapping["usable_as_authority"] is False
    assert mapping["content_retained_for_operator_and_laboratory"] is True
    assert mapping["content_copied_into_authoritative_request"] is False


def test_projection_updates_existing_laboratory_command_idempotently() -> None:
    projection = subject.build_copilot_advisory_laboratory_projection(
        _intake_mapping()
    )
    smoke = _command().smoke

    first = subject._project_into_smoke_command(
        smoke,
        projection,
        inject_context_ref=True,
        increment_context_generation=True,
    )
    second = subject._project_into_smoke_command(
        first,
        projection,
        inject_context_ref=True,
        increment_context_generation=True,
    )

    first_deliberation = first.laboratory.deliberation
    second_deliberation = second.laboratory.deliberation
    assert projection.context_ref in first_deliberation.orientation.context_refs
    assert first_deliberation.context_generation == 1
    assert second_deliberation.context_generation == 1
    assert second_deliberation.orientation.context_refs.count(
        projection.context_ref
    ) == 1
    assert (
        first_deliberation.source_candidate_ref
        == "source-candidate:github-request-0123456789abcdef"
    )
    assert any(
        "consultative hypothesis" in directive
        for directive in first_deliberation.orientation.do_directives
    )
    assert any(
        "publication authorization" in directive
        for directive in first_deliberation.orientation.avoid_directives
    )


def test_operator_projection_delegates_to_existing_smoke(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_intake(*args, **kwargs):
        return IntakeResult(True, (), _intake_mapping())

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
    assert result.advisory_present is True
    assert result.advisory_injected is True
    assert result.github_mutation_performed is False
    assert result.scheduler_created is False
    assert result.publication_preview["publication_gate_required"] is True
    assert result.publication_preview["summary"].startswith("Comparer")
    effective = captured["command"]
    assert effective is not _command().smoke
    assert effective.policy_decision_id == "policy:test:0281-r5"


def test_required_missing_advisory_blocks_before_laboratory(
    monkeypatch,
) -> None:
    called = False

    def fake_intake(*args, **kwargs):
        return IntakeResult(True, (), _intake_mapping(with_advisory=False))

    async def fail_laboratory(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("laboratory must not run")

    monkeypatch.setattr(
        subject,
        "run_github_dual_artifact_source_candidate_intake",
        fake_intake,
    )
    monkeypatch.setattr(
        subject,
        "run_github_dual_artifact_laboratory_smoke",
        fail_laboratory,
    )

    result = asyncio.run(
        subject.run_github_operator_laboratory_advisory_projection(
            object(),
            b"request",
            b"manifest",
            None,
            _command(),
        )
    )

    assert result.valid is False
    assert result.issues == ("validated Copilot advisory is required",)
    assert called is False


def test_command_requires_operator_policy_and_promote_or_merge() -> None:
    bad_policy = GitHubDualArtifactLaboratorySmokeCommand(
        decision=Decision(),
        laboratory=Laboratory(),
        policy_decision_id="not-policy",
    )
    try:
        subject.GitHubOperatorLaboratoryAdvisoryProjectionCommand(
            smoke=bad_policy
        )
    except ValueError as exc:
        assert "policy:" in str(exc)
    else:
        raise AssertionError("bad policy id must be rejected")

    try:
        GitHubDualArtifactLaboratorySmokeCommand(
            decision=Decision(action="inspect"),
            laboratory=Laboratory(),
            policy_decision_id="policy:test",
        )
    except ValueError as exc:
        assert "promote or merge" in str(exc)
    else:
        raise AssertionError(
            "the existing 0275 smoke must reject inspect"
        )
