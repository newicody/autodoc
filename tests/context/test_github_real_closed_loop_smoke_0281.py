from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import context.github_real_closed_loop_smoke_0281 as subject


def _write_imported_run(raw_path: Path, index_path: Path):
    repository = "newicody/projects"
    run_id = "29246131317"
    slug = "newicody__projects"
    files = (
        ("100", "autodoc-authoritative-request", "authoritative_request.json", b"request"),
        ("200", "autodoc-copilot-advisory", "copilot_advisory.json", b"advisory"),
        ("300", "autodoc-dual-artifact-manifest", "dual_artifact_manifest.json", b"manifest"),
    )
    collected = []
    for artifact_id, artifact_name, filename, content in files:
        path = raw_path / slug / run_id / artifact_id / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        collected.append({
            "artifact_name": artifact_name,
            "filename": filename,
            "relative_path": f"{artifact_id}/{filename}",
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        })
    report = {
        "schema": "missipy.github.dual_artifact_fetch_run_group.v1",
        "status": "ready",
        "repository": repository,
        "run_id": run_id,
        "collected_files": collected,
        "assembly": {"valid": True},
    }
    report_path = (
        index_path / "github_dual_artifact_run_groups" / slug / f"{run_id}.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report), encoding="utf-8")
    return subject.load_imported_github_run_bundle(
        dataset_raw_path=raw_path,
        dataset_index_path=index_path,
        repository=repository,
        run_id=run_id,
    )


def _command(bundle):
    return subject.GitHubRealClosedLoopSmokeCommand(
        repository="newicody/projects",
        run_id="29246131317",
        issue_number=15,
        members=bundle.members,
        run_group_report_ref=bundle.report_ref,
        policy_decision_id="policy:0281:r7:test",
        operator_reason="operator approved",
    )


def _assembly_mapping():
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


def test_imported_bundle_uses_ready_report_and_raw_dataset(tmp_path: Path) -> None:
    bundle = _write_imported_run(tmp_path / "raw", tmp_path / "index")
    assert bundle.report_ref.startswith(
        "dataset-index:github-dual-artifact-run-group:"
    )
    assert {member.filename for member in bundle.members} == {
        "authoritative_request.json",
        "copilot_advisory.json",
        "dual_artifact_manifest.json",
    }


def test_imported_bundle_rejects_digest_mismatch(tmp_path: Path) -> None:
    bundle = _write_imported_run(tmp_path / "raw", tmp_path / "index")
    (bundle.raw_run_root / "100" / "authoritative_request.json").write_bytes(
        b"changed"
    )
    try:
        subject.load_imported_github_run_bundle(
            dataset_raw_path=tmp_path / "raw",
            dataset_index_path=tmp_path / "index",
            repository="newicody/projects",
            run_id="29246131317",
        )
    except ValueError as exc:
        assert "mismatch" in str(exc)
    else:
        raise AssertionError("digest mismatch must be rejected")


def test_real_smoke_composes_without_mutation(tmp_path: Path, monkeypatch) -> None:
    bundle = _write_imported_run(tmp_path / "raw", tmp_path / "index")
    assembly = SimpleNamespace(
        valid=True,
        issues=(),
        to_mapping=lambda: _assembly_mapping(),
    )
    projection_mapping = {
        "valid": True,
        "issues": [],
        "publication_preview": {
            "schema": "missipy.github.copilot_advisory_publication_preview.v1",
            "source_candidate_ref": "github-request-0123456789abcdef",
            "advisory_context_ref": "ctx:github-advisory:0123456789abcdef01234567",
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
            _command(bundle),
            store=object(),
        )
    )
    assert result.valid is True
    assert result.run_group_report_ref == bundle.report_ref
    assert result.publication_plan["action"] == "create"
    assert result.existing_scheduler_used is True
    assert result.github_mutation_performed is False
