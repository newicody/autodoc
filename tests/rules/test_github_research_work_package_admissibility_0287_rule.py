from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.github_research_work_package_admissibility_0287 import (
    GitHubResearchWorkPackageAdmissibilityCommand,
    evaluate_github_research_work_package_admissibility,
)


def _package() -> dict[str, object]:
    return {
        "schema": "missipy.research.correlated_work_package.v1",
        "work_package_ref": "research-work-package:0123456789abcdef01234567",
        "repository": "newicody/projects",
        "run_id": "29622831972",
        "source_issue": {
            "number": 15,
            "url": "https://github.com/newicody/projects/issues/15",
        },
        "origin_frame_id": "github:issue:newicody/projects:15",
        "ticket_revision_id": "ticket-revision:15:1",
        "source_candidate_ref": "source-candidate:15",
        "conversation_ref": "conversation:research:15",
        "return_route_ref": "return-route:github:15",
        "context_generation": 0,
        "context_refs": ["context:github-issue:15"],
        "evidence_refs": ["github-actions-run:29622831972"],
        "authoritative_request": {
            "schema": "missipy.github.authoritative_request.v1",
            "authoritative": True,
            "advisory_content_embedded": False,
            "remote_mutation_requested": False,
            "repository": "newicody/projects",
            "issue_number": 15,
            "metadata": {
                "requested_status": "Recherche",
                "request_mode": "initial",
                "parent_event_ref": "",
            },
        },
        "correlation_manifest": {
            "schema": "missipy.github.dual_artifact_manifest.v1",
            "request_is_authority": True,
            "advisory_is_authority": False,
        },
        "copilot_advisory": {
            "schema": "missipy.github.copilot_advisory.v2",
            "trusted": False,
            "usable_as_hint": True,
            "usable_as_authority": False,
        },
        "advisory_present": True,
        "request_authoritative": True,
        "advisory_used_as_hint_only": True,
        "ready_for_laboratory_route": True,
        "scheduler_route_created": False,
        "sql_write_performed": False,
        "qdrant_write_performed": False,
        "github_mutation_performed": False,
    }


def _evaluate(package: dict[str, object]):
    return evaluate_github_research_work_package_admissibility(
        GitHubResearchWorkPackageAdmissibilityCommand(work_package=package)
    )


def test_dedicated_research_package_becomes_route_candidate_without_dispatch() -> None:
    result = _evaluate(_package())
    payload = result.to_mapping()

    assert result.admissible is True
    assert result.status == "admissible"
    assert payload["route_candidate"]["schema"] == (
        "missipy.github.research_laboratory_route_candidate.v1"
    )
    assert payload["route_candidate"]["repository"] == "newicody/projects"
    assert payload["route_candidate"]["requested_status"] == "Recherche"
    assert payload["scheduler_command_created"] is False
    assert payload["scheduler_dispatch_started"] is False
    assert payload["laboratory_execution_started"] is False
    assert payload["sql_write_performed"] is False
    assert payload["qdrant_write_performed"] is False


def test_repository_other_than_projects_is_inadmissible() -> None:
    package = _package()
    package["repository"] = "newicody/autodoc"
    request = package["authoritative_request"]
    assert isinstance(request, dict)
    request["repository"] = "newicody/autodoc"

    result = _evaluate(package)

    assert result.admissible is False
    assert any("dedicated research repository" in issue for issue in result.issues)


def test_missing_explicit_research_status_is_inadmissible() -> None:
    package = _package()
    request = package["authoritative_request"]
    assert isinstance(request, dict)
    metadata = request["metadata"]
    assert isinstance(metadata, dict)
    metadata.pop("requested_status")

    result = _evaluate(package)

    assert result.admissible is False
    assert any("requested_status" in issue for issue in result.issues)


def test_continuation_requires_parent_reference() -> None:
    package = _package()
    request = package["authoritative_request"]
    assert isinstance(request, dict)
    metadata = request["metadata"]
    assert isinstance(metadata, dict)
    metadata["request_mode"] = "continuation"

    result = _evaluate(package)

    assert result.admissible is False
    assert "a continuation research request requires parent_event_ref" in result.issues


def test_initial_request_rejects_parent_reference() -> None:
    package = _package()
    request = package["authoritative_request"]
    assert isinstance(request, dict)
    metadata = request["metadata"]
    assert isinstance(metadata, dict)
    metadata["parent_event_ref"] = "github-actions-run:1"

    result = _evaluate(package)

    assert result.admissible is False
    assert "an initial research request must not carry parent_event_ref" in result.issues


def test_advisory_is_required_but_never_authoritative() -> None:
    missing = _package()
    missing["copilot_advisory"] = {}
    missing["advisory_present"] = False
    result = _evaluate(missing)
    assert result.admissible is False
    assert "the correlated Copilot advisory is required" in result.issues

    authoritative = deepcopy(_package())
    advisory = authoritative["copilot_advisory"]
    assert isinstance(advisory, dict)
    advisory["usable_as_authority"] = True
    result = _evaluate(authoritative)
    assert result.admissible is False
    assert "usable_as_authority must be False" in result.issues


def test_route_candidate_digest_is_deterministic() -> None:
    first = _evaluate(_package()).to_mapping()["route_candidate"]
    second = _evaluate(_package()).to_mapping()["route_candidate"]

    assert first["route_candidate_ref"] == second["route_candidate_ref"]
    assert first["admissibility_digest"] == second["admissibility_digest"]


def test_rule_keeps_fetch_scheduler_and_laboratory_boundaries_separate() -> None:
    module = (
        ROOT
        / "src/context/github_research_work_package_admissibility_0287.py"
    ).read_text(encoding="utf-8")
    tool = (
        ROOT
        / "tools/check_github_research_work_package_admissibility_0287.py"
    ).read_text(encoding="utf-8")

    assert "CorrelatedResearchWorkPackage" in module
    assert "existing_work_package_reused" in module
    assert "artifact_digest_validation_duplicated" in module
    assert "scheduler_dispatch_started" in module
    assert "laboratory_execution_started" in module
    assert "while True" not in module
    assert "while True" not in tool
    assert "subprocess" not in module
    assert "subprocess" not in tool
    assert "psycopg" not in module
    assert "import qdrant" not in module.lower()
    assert "from qdrant" not in module.lower()
    assert "urlopen" not in module
