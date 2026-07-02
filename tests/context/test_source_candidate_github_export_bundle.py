from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.source_candidate_github_export_bundle import (
    SourceCandidateGithubExportBundlePolicy,
    build_source_candidate_github_export_bundle,
    read_source_candidate_github_export_bundle_manifest,
)
from context.source_candidate_remote_mutation_gate import SourceCandidateRemoteMutationGatePolicy


def _write_contract(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.external_projection_contract.v1",
                "target_kind": "github_project_surface",
                "source_handoff_path": "/tmp/handoff",
                "gate_passed": True,
                "projection_allowed": True,
                "blocked_reasons": [],
                "item_count": 1,
                "items": [],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_payload(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.github_projection_payload.v1",
                "repository": "newicody/autodoc",
                "project_key": None,
                "dry_run": True,
                "remote_mutation": False,
                "projection_allowed": True,
                "blocked_reasons": [],
                "operation_count": 1,
                "operations": [
                    {
                        "action": "create_issue",
                        "candidate_id": "candidate-a",
                        "title": "SourceCandidate: Ready",
                        "body": "dry-run body",
                        "labels": ["autodoc", "source-candidate", "dry-run"],
                        "safety_flags": [],
                    }
                ],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _open_gate_policy() -> SourceCandidateRemoteMutationGatePolicy:
    return SourceCandidateRemoteMutationGatePolicy(
        remote_mutation_enabled=True,
        operator_confirmed=True,
        allowed_repositories=("newicody/autodoc",),
    )


def test_github_export_bundle_writes_local_artifacts(tmp_path: Path) -> None:
    contract = tmp_path / "external_projection_contract.json"
    payload = tmp_path / "github_projection_payload.json"
    bundle_dir = tmp_path / "github_export_bundle"
    _write_contract(contract)
    _write_payload(payload)

    bundle = build_source_candidate_github_export_bundle(
        contract_path=contract,
        github_payload_path=payload,
        policy=SourceCandidateGithubExportBundlePolicy(path=bundle_dir),
    )

    assert bundle.path == bundle_dir
    assert bundle.repository == "newicody/autodoc"
    assert bundle.dry_run is True
    assert bundle.mutation_allowed is False
    assert bundle.operation_count == 1
    assert bundle.artifact_count == 5
    assert (bundle_dir / "manifest.json").exists()
    assert (bundle_dir / "external_projection_contract.json").exists()
    assert (bundle_dir / "github_projection_payload.json").exists()
    assert (bundle_dir / "remote_mutation_gate.json").exists()
    assert (bundle_dir / "github_adapter_dry_run.json").exists()


def test_github_export_bundle_can_record_open_gate_result(tmp_path: Path) -> None:
    contract = tmp_path / "external_projection_contract.json"
    payload = tmp_path / "github_projection_payload.json"
    bundle_dir = tmp_path / "github_export_bundle"
    _write_contract(contract)
    _write_payload(payload)

    bundle = build_source_candidate_github_export_bundle(
        contract_path=contract,
        github_payload_path=payload,
        policy=SourceCandidateGithubExportBundlePolicy(
            path=bundle_dir,
            gate_policy=_open_gate_policy(),
        ),
    )

    assert bundle.mutation_allowed is True
    gate = json.loads((bundle_dir / "remote_mutation_gate.json").read_text(encoding="utf-8"))
    adapter = json.loads((bundle_dir / "github_adapter_dry_run.json").read_text(encoding="utf-8"))
    assert gate["mutation_allowed"] is True
    assert adapter["gate"]["mutation_allowed"] is True


def test_github_export_bundle_manifest_can_be_read(tmp_path: Path) -> None:
    contract = tmp_path / "external_projection_contract.json"
    payload = tmp_path / "github_projection_payload.json"
    bundle_dir = tmp_path / "github_export_bundle"
    _write_contract(contract)
    _write_payload(payload)

    bundle = build_source_candidate_github_export_bundle(
        contract_path=contract,
        github_payload_path=payload,
        policy=SourceCandidateGithubExportBundlePolicy(path=bundle_dir),
    )

    manifest = read_source_candidate_github_export_bundle_manifest(bundle.manifest_path)

    assert manifest["schema"] == "missipy.source_candidate.github_export_bundle.v1"
    assert manifest["repository"] == "newicody/autodoc"
    assert manifest["artifact_count"] == 4


def test_github_export_bundle_rejects_conflicting_names(tmp_path: Path) -> None:
    contract = tmp_path / "external_projection_contract.json"
    payload = tmp_path / "github_projection_payload.json"
    _write_contract(contract)
    _write_payload(payload)

    with pytest.raises(ValueError, match="distinct"):
        build_source_candidate_github_export_bundle(
            contract_path=contract,
            github_payload_path=payload,
            policy=SourceCandidateGithubExportBundlePolicy(
                path=tmp_path / "bundle",
                contract_name="same.json",
                payload_name="same.json",
            ),
        )
