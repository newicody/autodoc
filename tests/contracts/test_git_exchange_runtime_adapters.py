from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tools.build_git_exchange_initial_envelope import main as build_initial_main


def test_initial_envelope_builder_wraps_existing_v2_advisory(tmp_path: Path):
    advisory = {
        "schema": "missipy.github.copilot_advisory.v2",
        "artifact_ref": "advisory:abc",
        "request_artifact_ref": "request:abc",
        "concrete_objective": "Study",
        "expected_result": "Report",
        "provided_constraints": [],
        "success_criteria": ["Evidence"],
        "trusted": False,
        "usable_as_authority": False,
    }
    source = tmp_path / "advisory.json"
    output = tmp_path / "envelope.json"
    source.write_text(json.dumps(advisory), encoding="utf-8")
    assert build_initial_main([
        "--advisory", str(source),
        "--repository", "newicody/projects",
        "--issue-number", "7",
        "--output", str(output),
    ]) == 0
    envelope = json.loads(output.read_text(encoding="utf-8"))
    assert envelope["role"] == "copilot_initial"
    assert envelope["transport"] == "git_commit_push"
    assert envelope["payload"] == advisory
    assert envelope["execution_authorized"] is False


def test_refinement_parser_accepts_only_explicit_scientific_fields():
    from tools.run_autodoc_copilot_refinement import _extract

    value = _extract(json.dumps({
        "concrete_objective": "Study",
        "expected_result": "Report",
        "provided_constraints": ["No GPU"],
        "success_criteria": ["Traceable evidence"],
        "scientific_representations": ["Table", "Curve"],
    }))
    assert value["scientific_representations"] == ["Table", "Curve"]


def test_refinement_parser_rejects_extra_authority_or_route_fields():
    from tools.run_autodoc_copilot_refinement import _extract

    with pytest.raises(ValueError, match="strict schema"):
        _extract(json.dumps({
            "concrete_objective": "Study",
            "expected_result": "Report",
            "provided_constraints": [],
            "success_criteria": ["Evidence"],
            "scientific_representations": ["Table"],
            "scheduler_command": "run",
        }))
