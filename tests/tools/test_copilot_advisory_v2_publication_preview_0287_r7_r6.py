from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "templates/github/projects-repository/scripts/"
    "build_copilot_advisory_v2_publication_preview.py"
)


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("copilot_v2_preview", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_artifacts(tmp_path: Path) -> tuple[Path, Path, Path]:
    request = {
        "schema": "missipy.github.authoritative_request.v1",
        "origin_frame_id": "frame:1",
        "ticket_revision_id": "ticket:1",
        "artifact_ref": "request:1",
        "repository": "newicody/projects",
        "issue_number": 7,
        "authoritative": True,
    }
    advisory = {
        "schema": "missipy.github.copilot_advisory.v2",
        "origin_frame_id": "frame:1",
        "ticket_revision_id": "ticket:1",
        "request_artifact_ref": "request:1",
        "artifact_ref": "advisory:1",
        "prompt_digest": "b" * 64,
        "response_digest": "c" * 64,
        "concrete_objective": "Étudier la demande.",
        "expected_result": "Un résultat observable.",
        "provided_constraints": ["Rester consultatif."],
        "success_criteria": ["Le résultat est publié."],
        "trusted": False,
        "usable_as_hint": True,
        "usable_as_authority": False,
    }
    request_path = tmp_path / "request.json"
    advisory_path = tmp_path / "advisory.json"
    manifest_path = tmp_path / "manifest.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    advisory_path.write_text(json.dumps(advisory), encoding="utf-8")
    manifest = {
        "schema": "missipy.github.dual_artifact_manifest.v1",
        "origin_frame_id": "frame:1",
        "ticket_revision_id": "ticket:1",
        "request_artifact_ref": "request:1",
        "advisory_artifact_ref": "advisory:1",
        "request_is_authority": True,
        "advisory_is_authority": False,
        "request_sha256": hashlib.sha256(request_path.read_bytes()).hexdigest(),
        "advisory_sha256": hashlib.sha256(advisory_path.read_bytes()).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return advisory_path, request_path, manifest_path


def test_preview_preserves_four_fields_and_builds_board_summary(tmp_path: Path) -> None:
    module = _load()
    advisory, request, manifest = _write_artifacts(tmp_path)
    preview = module.build_copilot_advisory_v2_publication_preview(
        advisory_path=advisory,
        request_path=request,
        manifest_path=manifest,
        run_id="99",
        repository="newicody/projects",
        issue_number=7,
    )
    assert preview["schema"].endswith("preview.v2")
    assert preview["concrete_objective"] == "Étudier la demande."
    assert preview["advisory_is_authority"] is False
    summary = module.render_projectv2_v2_summary(preview)
    assert "Objectif:" in summary
    assert "Résultat attendu:" in summary
    assert "Critères:" in summary


def test_preview_rejects_digest_or_schema_drift(tmp_path: Path) -> None:
    module = _load()
    advisory, request, manifest = _write_artifacts(tmp_path)
    payload = json.loads(advisory.read_text(encoding="utf-8"))
    payload["schema"] = "missipy.github.copilot_advisory.v1"
    advisory.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected Copilot advisory schema"):
        module.build_copilot_advisory_v2_publication_preview(
            advisory_path=advisory,
            request_path=request,
            manifest_path=manifest,
            run_id="99",
            repository="newicody/projects",
            issue_number=7,
        )
