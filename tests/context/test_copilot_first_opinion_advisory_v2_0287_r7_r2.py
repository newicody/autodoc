from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "templates/github/scripts/run_autodoc_copilot_advisory.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("copilot_advisory_v2", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _request() -> dict[str, object]:
    return {
        "schema": "missipy.github.authoritative_request.v1",
        "origin_frame_id": "frame:0287-r7-r2",
        "ticket_revision_id": "ticket-revision:42",
        "artifact_ref": "github-request:42",
        "title": "Brancher le premier avis Copilot",
        "body": "Produire quatre résultats observables sans ajouter de route.",
        "labels": ["research", "copilot"],
        "autodoc_dispatch": {"mode": "review"},
        "context": {"theme": "github-projects"},
    }


def _first_opinion() -> dict[str, object]:
    return {
        "concrete_objective": "Brancher un premier avis structuré.",
        "expected_result": "Un artefact v2 validé et corrélé.",
        "provided_constraints": [
            "Conserver Copilot non autoritatif.",
            "Ne pas ajouter de Scheduler.",
        ],
        "success_criteria": [
            "Le schéma v2 contient exactement quatre champs analytiques.",
            "Un JSON invalide ne produit aucun artefact.",
        ],
    }


def test_historical_v1_extraction_remains_available() -> None:
    module = _load_script()
    historical = {
        "summary": "Historical advisory",
        "suggested_route": "review",
        "assumptions": [],
        "questions": [],
        "risks": [],
        "confidence": 0.5,
    }

    assert module.extract_advisory(json.dumps(historical)) == historical


def test_v2_parser_requires_exactly_four_analytical_fields() -> None:
    module = _load_script()
    opinion = _first_opinion()

    assert module.extract_first_opinion(json.dumps(opinion)) == opinion

    with pytest.raises(ValueError, match="field mismatch"):
        module.extract_first_opinion(
            json.dumps({**opinion, "suggested_route": "develop"})
        )

    with pytest.raises(ValueError, match="success_criteria"):
        module.extract_first_opinion(
            json.dumps({**opinion, "success_criteria": []})
        )


def test_main_wires_issue_content_and_writes_v2_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_script()
    request_path = tmp_path / "authoritative_request.json"
    output_path = tmp_path / "copilot_advisory.json"
    request_path.write_text(json.dumps(_request()), encoding="utf-8")
    captured: dict[str, object] = {}
    event = {"type": "assistant.message", "content": json.dumps(_first_opinion())}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(event), stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setenv("AUTODOC_REQUEST", str(request_path))
    monkeypatch.setenv("AUTODOC_ADVISORY", str(output_path))
    monkeypatch.setenv("AUTODOC_COPILOT_COMMAND", "fake-copilot")
    monkeypatch.setenv("AUTODOC_COPILOT_REQUIRED", "true")

    assert module.main() == 0
    command = captured["command"]
    assert isinstance(command, list)
    prompt = command[command.index("-p") + 1]
    assert _request()["title"] in prompt
    assert _request()["body"] in prompt
    assert "research" in prompt
    assert "autodoc_dispatch" in prompt
    assert "github-projects" in prompt
    assert "exactly these four fields" in prompt
    assert "suggested_route" not in prompt
    assert "confidence" in prompt
    assert "Do not add" in prompt

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "missipy.github.copilot_advisory.v2"
    analytical_keys = {
        "concrete_objective",
        "expected_result",
        "provided_constraints",
        "success_criteria",
    }
    assert analytical_keys <= payload.keys()
    for old_key in (
        "summary",
        "suggested_route",
        "assumptions",
        "questions",
        "risks",
        "confidence",
    ):
        assert old_key not in payload
    assert payload["trusted"] is False
    assert payload["usable_as_hint"] is True
    assert payload["usable_as_authority"] is False
    assert payload["request_artifact_ref"] == "github-request:42"


def test_invalid_v2_response_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_script()
    request_path = tmp_path / "authoritative_request.json"
    output_path = tmp_path / "copilot_advisory.json"
    request_path.write_text(json.dumps(_request()), encoding="utf-8")

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps({"summary": "old contract"}),
            stderr="",
        )

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setenv("AUTODOC_REQUEST", str(request_path))
    monkeypatch.setenv("AUTODOC_ADVISORY", str(output_path))
    monkeypatch.setenv("AUTODOC_COPILOT_REQUIRED", "true")

    assert module.main() == 1
    assert not output_path.exists()
