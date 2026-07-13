from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import context.github_real_closed_loop_smoke_0281 as subject
from context.github_dual_artifact_run_assembly_0281 import (
    GitHubDualArtifactRunMember,
)


def _members() -> tuple[GitHubDualArtifactRunMember, ...]:
    return (
        GitHubDualArtifactRunMember(
            "autodoc-authoritative-request",
            "authoritative_request.json",
            b"request",
        ),
        GitHubDualArtifactRunMember(
            "autodoc-copilot-advisory",
            "copilot_advisory.json",
            b"advisory",
        ),
        GitHubDualArtifactRunMember(
            "autodoc-dual-artifact-manifest",
            "dual_artifact_manifest.json",
            b"manifest",
        ),
    )


def _command() -> subject.GitHubRealClosedLoopSmokeCommand:
    return subject.GitHubRealClosedLoopSmokeCommand(
        repository="newicody/projects",
        run_id="29246131317",
        issue_number=15,
        members=_members(),
        policy_decision_id="policy:0281:r7:test",
        operator_reason="operator approved",
    )


def _assembly_mapping() -> dict[str, object]:
    return {
        "valid": True,
        "issues": [],
        "intake": {
            "request": {
                "repository": "newicody/projects",
                "issue_number": 15,
                "title": "Recherche réelle",
                "body": "Comparer les solutions.",
                "artifact_ref": "github-request:newicody/projects:15:abc",
            },
            "source_candidate": {
                "candidate_id": "github-request-0123456789abcdef",
            },
        },
    }


def test_collect_members_from_gh_run_download_tree(tmp_path: Path) -> None:
    for directory, filename in (
        ("autodoc-authoritative-request", "authoritative_request.json"),
        ("autodoc-copilot-advisory", "copilot_advisory.json"),
        ("autodoc-dual-artifact-manifest", "dual_artifact_manifest.json"),
    ):
        path = tmp_path / directory / filename
        path.parent.mkdir()
        path.write_text("{}", encoding="utf-8")

    members = subject.collect_github_run_members(tmp_path)

    assert {member.filename for member in members} == {
        "authoritative_request.json",
        "copilot_advisory.json",
        "dual_artifact_manifest.json",
    }


def test_laboratory_command_is_built_for_existing_0274_path() -> None:
    command = subject.build_real_closed_loop_laboratory_command(
        _command(),
        request=_assembly_mapping()["intake"]["request"],
        source_candidate=_assembly_mapping()["intake"]["source_candidate"],
    )

    deliberation = command.deliberation
    assert deliberation.orientation.orientation_ref.startswith(
        "orientation:github-run:"
    )
    assert deliberation.artifact_ref.startswith("artifact:github-request:")
    assert deliberation.source_candidate_ref == (
        "source-candidate:github-request-0123456789abcdef"
    )
    assert deliberation.target_ref == "github:issue:newicody/projects/15"
    assert command.handoff.execute is True
    assert command.handoff.vector_execute is True
    assert command.recall.execute is True
    assert command.verify_sql_replay is True


def test_real_smoke_composes_r2_r5_and_r6_without_mutation(
    monkeypatch,
) -> None:
    assembly = SimpleNamespace(
        valid=True,
        issues=(),
        to_mapping=lambda: _assembly_mapping(),
    )
    projection_mapping = {
        "valid": True,
        "issues": [],
        "publication_preview": {
            "schema": (
                "missipy.github.copilot_advisory_publication_preview.v1"
            ),
            "source_candidate_ref": "github-request-0123456789abcdef",
            "advisory_context_ref": (
                "ctx:github-advisory:0123456789abcdef01234567"
            ),
            "advisory_artifact_ref": "github-advisory:abc",
            "summary": "Résumé",
            "suggested_route": "Route",
            "questions": [],
            "risks": [],
            "confidence": 0.7,
            "advisory_is_authority": False,
            "operator_decision_required": True,
            "publication_gate_required": True,
            "github_mutation_performed": False,
        },
        "github_mutation_performed": False,
        "scheduler_created": False,
    }
    projection = SimpleNamespace(
        valid=True,
        issues=(),
        to_mapping=lambda: projection_mapping,
    )
    plan = SimpleNamespace(
        valid=True,
        action="create",
        issues=(),
        to_mapping=lambda: {
            "valid": True,
            "action": "create",
            "plan_digest": "d" * 64,
            "github_mutation_performed": False,
        },
    )

    monkeypatch.setattr(
        subject,
        "run_github_dual_artifact_run_assembly",
        lambda *args, **kwargs: assembly,
    )

    async def fake_projection(*args, **kwargs):
        return projection

    monkeypatch.setattr(
        subject,
        "run_github_operator_laboratory_advisory_projection",
        fake_projection,
    )
    monkeypatch.setattr(
        subject,
        "plan_github_controlled_advisory_issue_publication",
        lambda *args, **kwargs: plan,
    )

    result = asyncio.run(
        subject.run_github_real_closed_loop_smoke(
            object(),
            _command(),
            store=object(),
        )
    )

    assert result.valid is True
    assert result.publication_preview["summary"] == "Résumé"
    assert result.publication_plan["action"] == "create"
    assert result.existing_scheduler_used is True
    assert result.scheduler_created is False
    assert result.github_mutation_performed is False


def test_identity_mismatch_stops_before_laboratory(monkeypatch) -> None:
    mapping = _assembly_mapping()
    mapping["intake"]["request"]["issue_number"] = 99
    assembly = SimpleNamespace(
        valid=True,
        issues=(),
        to_mapping=lambda: mapping,
    )
    called = False

    monkeypatch.setattr(
        subject,
        "run_github_dual_artifact_run_assembly",
        lambda *args, **kwargs: assembly,
    )

    async def fail_projection(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("laboratory must not run")

    monkeypatch.setattr(
        subject,
        "run_github_operator_laboratory_advisory_projection",
        fail_projection,
    )

    result = asyncio.run(
        subject.run_github_real_closed_loop_smoke(
            object(),
            _command(),
        )
    )

    assert result.valid is False
    assert "issue_number" in result.issues[0]
    assert called is False
