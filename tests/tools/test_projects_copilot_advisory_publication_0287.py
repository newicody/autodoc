from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "templates/github/projects-repository/scripts/"
    "build_copilot_advisory_publication_preview.py"
)


def _module():
    spec = importlib.util.spec_from_file_location(
        "build_copilot_preview_0287",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, payload: dict) -> Path:
    path.write_text(
        json.dumps(payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _fixtures(tmp_path: Path):
    request = {
        "schema": "missipy.github.authoritative_request.v1",
        "origin_frame_id": "frame:1",
        "ticket_revision_id": "ticket-revision:1",
        "artifact_ref": "github-request:abc",
        "repository": "newicody/projects",
        "issue_number": 12,
        "authoritative": True,
    }
    advisory = {
        "schema": "missipy.github.copilot_advisory.v1",
        "origin_frame_id": "frame:1",
        "ticket_revision_id": "ticket-revision:1",
        "artifact_ref": "github-advisory:def",
        "request_artifact_ref": "github-request:abc",
        "prompt_digest": "a" * 64,
        "response_digest": "b" * 64,
        "summary": "Résumé Copilot",
        "suggested_route": "Revoir le contrat",
        "assumptions": ["A"],
        "questions": ["Q"],
        "risks": ["R"],
        "confidence": 0.75,
        "trusted": False,
        "usable_as_hint": True,
        "usable_as_authority": False,
    }
    request_path = _write(tmp_path / "authoritative_request.json", request)
    advisory_path = _write(tmp_path / "copilot_advisory.json", advisory)
    manifest = {
        "schema": "missipy.github.dual_artifact_manifest.v1",
        "origin_frame_id": "frame:1",
        "ticket_revision_id": "ticket-revision:1",
        "request_artifact_ref": "github-request:abc",
        "request_sha256": sha256(request_path.read_bytes()).hexdigest(),
        "advisory_artifact_ref": "github-advisory:def",
        "advisory_sha256": sha256(advisory_path.read_bytes()).hexdigest(),
        "request_is_authority": True,
        "advisory_is_authority": False,
    }
    manifest_path = _write(
        tmp_path / "dual_artifact_manifest.json",
        manifest,
    )
    return advisory_path, request_path, manifest_path


def test_builds_non_authoritative_correlated_preview(tmp_path: Path):
    module = _module()
    advisory, request, manifest = _fixtures(tmp_path)
    preview = module.build_copilot_advisory_publication_preview(
        advisory_path=advisory,
        request_path=request,
        manifest_path=manifest,
        run_id="123",
        repository="newicody/projects",
        issue_number=12,
    )
    assert preview["schema"] == (
        "missipy.github.copilot_advisory_publication_preview.v1"
    )
    assert preview["summary"] == "Résumé Copilot"
    assert preview["confidence"] == 0.75
    assert preview["operator_decision_required"] is True
    assert preview["publication_gate_required"] is True
    assert preview["github_mutation_performed"] is False
    assert preview["advisory_is_authority"] is False


def test_rejects_digest_mismatch(tmp_path: Path):
    module = _module()
    advisory, request, manifest = _fixtures(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["advisory_sha256"] = "0" * 64
    _write(manifest, payload)
    with pytest.raises(ValueError, match="advisory digest mismatch"):
        module.build_copilot_advisory_publication_preview(
            advisory_path=advisory,
            request_path=request,
            manifest_path=manifest,
            run_id="123",
            repository="newicody/projects",
            issue_number=12,
        )


def test_rejects_issue_mismatch(tmp_path: Path):
    module = _module()
    advisory, request, manifest = _fixtures(tmp_path)
    with pytest.raises(ValueError, match="Issue mismatch"):
        module.build_copilot_advisory_publication_preview(
            advisory_path=advisory,
            request_path=request,
            manifest_path=manifest,
            run_id="123",
            repository="newicody/projects",
            issue_number=13,
        )
