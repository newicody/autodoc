from __future__ import annotations

from types import SimpleNamespace

import pytest

import context.github_ready_run_research_admissibility_0287 as module
from context.github_ready_run_research_admissibility_0287 import (
    GitHubReadyRunArtifactContent,
    GitHubReadyRunResearchAdmissibilityCommand,
    assemble_ready_run_and_evaluate_research_admissibility,
)


def _ready_run() -> dict[str, object]:
    repository = "newicody/projects"
    run_id = "29622831972"
    return {
        "repository": repository,
        "run_id": run_id,
        "handoff_ref": "github-actions-ready-run:newicody-projects:29622831972",
        "status": "ready",
        "artifact_count": 3,
        "artifacts": {
            "authoritative_request": {
                "run_id": run_id,
                "artifact_id": "1",
                "artifact_name": "human--authoritative-request-v1",
                "availability": "downloaded",
            },
            "copilot_advisory": {
                "run_id": run_id,
                "artifact_id": "2",
                "artifact_name": "human--copilot-advisory-v2",
                "availability": "downloaded",
            },
            "run_manifest": {
                "run_id": run_id,
                "artifact_id": "3",
                "artifact_name": "human--run-manifest-v1",
                "availability": "downloaded",
            },
        },
        "local_execution_started": False,
        "remote_mutation_performed": False,
    }


def _contents() -> tuple[GitHubReadyRunArtifactContent, ...]:
    return (
        GitHubReadyRunArtifactContent(
            role="authoritative_request",
            content=b"request",
            artifact_id="1",
            source_artifact_name="human--authoritative-request-v1",
        ),
        GitHubReadyRunArtifactContent(
            role="copilot_advisory",
            content=b"advisory",
            artifact_id="2",
            source_artifact_name="human--copilot-advisory-v2",
        ),
        GitHubReadyRunArtifactContent(
            role="run_manifest",
            content=b"manifest",
            artifact_id="3",
            source_artifact_name="human--run-manifest-v1",
        ),
    )


def test_ready_run_boundaries_reject_missing_role_before_assembly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("assembly must not be called")

    monkeypatch.setattr(module, "run_github_dual_artifact_run_assembly", forbidden)
    ready = _ready_run()
    artifacts = dict(ready["artifacts"])
    artifacts.pop("run_manifest")
    ready["artifacts"] = artifacts

    result = assemble_ready_run_and_evaluate_research_admissibility(
        GitHubReadyRunResearchAdmissibilityCommand(
            ready_run=ready,
            artifact_contents=_contents(),
        )
    )

    assert result.valid is False
    assert result.status == "ready-run-invalid"
    assert called is False
    assert result.to_mapping()["scheduler_command_created"] is False
    assert result.to_mapping()["laboratory_execution_started"] is False


def test_existing_assembly_package_and_gate_are_reused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assembly_mapping = {
        "schema": "missipy.github.dual_artifact_run_assembly.v1",
        "valid": True,
        "intake": {
            "request": {
                "issue_number": 15,
            }
        },
    }
    work_package = {
        "schema": "missipy.research.correlated_work_package.v1",
        "work_package_ref": "research-work-package:test",
    }

    monkeypatch.setattr(
        module,
        "run_github_dual_artifact_run_assembly",
        lambda *args, **kwargs: SimpleNamespace(
            valid=True,
            issues=(),
            to_mapping=lambda: assembly_mapping,
        ),
    )
    monkeypatch.setattr(
        module,
        "build_correlated_research_work_package",
        lambda *args, **kwargs: SimpleNamespace(
            valid=True,
            issues=(),
            to_mapping=lambda: {
                "valid": True,
                "work_package": work_package,
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "evaluate_github_research_work_package_admissibility",
        lambda *args, **kwargs: SimpleNamespace(
            admissible=True,
            issues=(),
            to_mapping=lambda: {
                "valid": True,
                "admissible": True,
                "status": "admissible",
                "route_candidate": {
                    "route_candidate_ref": "research-route-candidate:test",
                },
            },
        ),
    )

    result = assemble_ready_run_and_evaluate_research_admissibility(
        GitHubReadyRunResearchAdmissibilityCommand(
            ready_run=_ready_run(),
            artifact_contents=_contents(),
        )
    )
    mapping = result.to_mapping()

    assert result.valid is True
    assert result.admissible is True
    assert result.status == "admissible"
    assert mapping["existing_dual_artifact_assembly_reused"] is True
    assert mapping["existing_correlated_work_package_reused"] is True
    assert mapping["existing_admissibility_gate_reused"] is True
    assert mapping["scheduler_command_created"] is False
    assert mapping["scheduler_dispatch_started"] is False
    assert mapping["laboratory_execution_started"] is False


def test_loaded_content_must_be_non_empty_bytes() -> None:
    with pytest.raises(TypeError):
        GitHubReadyRunArtifactContent(
            role="authoritative_request",
            content="not-bytes",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError):
        GitHubReadyRunArtifactContent(
            role="authoritative_request",
            content=b"",
        )


def test_command_remains_read_only() -> None:
    with pytest.raises(ValueError):
        GitHubReadyRunResearchAdmissibilityCommand(
            ready_run=_ready_run(),
            artifact_contents=_contents(),
            execute=True,
        )


def test_cli_is_local_read_only_and_does_not_import_scheduler() -> None:
    text = (
        module.__file__
        and __import__("pathlib").Path(module.__file__).read_text(encoding="utf-8")
    )
    assert "run_github_dual_artifact_run_assembly" in text
    assert "build_correlated_research_work_package" in text
    assert "evaluate_github_research_work_package_admissibility" in text
    assert "from kernel.scheduler" not in text
    assert "Scheduler(" not in text
