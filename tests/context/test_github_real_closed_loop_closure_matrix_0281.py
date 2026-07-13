from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import context.github_dual_artifact_run_assembly_0281 as assembly_subject
from context.github_controlled_advisory_issue_publication_0281 import (
    GitHubControlledAdvisoryIssuePublicationCommand,
    GitHubIssueCommentSnapshot,
    plan_github_controlled_advisory_issue_publication,
)
from context.github_dual_artifact_run_assembly_0281 import (
    GitHubDualArtifactRunAssemblyCommand,
    GitHubDualArtifactRunAssemblyPolicy,
    GitHubDualArtifactRunMember,
    run_github_dual_artifact_run_assembly,
)
from context.github_operator_laboratory_advisory_projection_0281 import (
    PUBLICATION_PREVIEW_SCHEMA,
)
from context.github_real_closed_loop_smoke_0281 import (
    load_imported_github_run_bundle,
)

REPOSITORY = "newicody/projects"
SLUG = "newicody__projects"
RUN_ID = "29253411918"


def _member(slot: str) -> GitHubDualArtifactRunMember:
    values = {
        "request": (
            "autodoc-authoritative-request",
            "authoritative_request.json",
            b'{"request":true}',
        ),
        "advisory": (
            "autodoc-copilot-advisory",
            "copilot_advisory.json",
            b'{"advisory":true}',
        ),
        "manifest": (
            "autodoc-dual-artifact-manifest",
            "dual_artifact_manifest.json",
            b'{"manifest":true}',
        ),
    }
    artifact_name, filename, content = values[slot]
    return GitHubDualArtifactRunMember(
        artifact_name, filename, content
    )


def _command(members):
    return GitHubDualArtifactRunAssemblyCommand(
        repository=REPOSITORY,
        run_id=RUN_ID,
        members=tuple(members),
    )


def test_advisory_absence_policy_is_explicit(monkeypatch) -> None:
    intake = SimpleNamespace(
        valid=True,
        issues=(),
        to_mapping=lambda: {
            "valid": True,
            "advisory": {},
            "github_mutation_performed": False,
        },
    )
    monkeypatch.setattr(
        assembly_subject,
        "run_github_dual_artifact_source_candidate_intake",
        lambda *args, **kwargs: intake,
    )
    members = (_member("request"), _member("manifest"))

    relaxed = run_github_dual_artifact_run_assembly(
        _command(members),
        GitHubDualArtifactRunAssemblyPolicy(
            allow_missing_advisory=True
        ),
    )
    strict = run_github_dual_artifact_run_assembly(
        _command(members),
        GitHubDualArtifactRunAssemblyPolicy(
            allow_missing_advisory=False
        ),
    )

    assert relaxed.valid is True
    assert relaxed.advisory_present is False
    assert relaxed.github_mutation_performed is False
    assert strict.valid is False
    assert (
        "Copilot advisory artifact member is required"
        in strict.issues
    )


@pytest.mark.parametrize("slot", ("request", "advisory", "manifest"))
def test_duplicate_artifact_member_is_rejected(slot: str) -> None:
    result = run_github_dual_artifact_run_assembly(
        _command(
            (
                _member("request"),
                _member("advisory"),
                _member("manifest"),
                _member(slot),
            )
        )
    )
    assert result.valid is False
    assert f"duplicate {slot} artifact member" in result.issues
    assert result.intake == {}
    assert result.filesystem_write_performed is False
    assert result.sql_write_performed is False
    assert result.qdrant_write_performed is False
    assert result.github_mutation_performed is False


def _entry(slot: str) -> dict[str, object]:
    member = _member(slot)
    return {
        "artifact_name": member.artifact_name,
        "filename": member.filename,
        "content": member.content,
    }


def _dataset(
    tmp_path: Path,
    entries: list[dict[str, object]],
) -> tuple[Path, Path]:
    raw = tmp_path / "raw"
    index = tmp_path / "index"
    root = raw / SLUG / RUN_ID
    root.mkdir(parents=True)
    collected = []
    for number, entry in enumerate(entries, 1):
        content = bytes(entry["content"])
        filename = str(entry["filename"])
        relative = Path(str(number)) / filename
        path = root / relative
        path.parent.mkdir()
        path.write_bytes(content)
        collected.append(
            {
                "artifact_name": entry["artifact_name"],
                "filename": filename,
                "relative_path": str(relative),
                "size_bytes": len(content),
                "sha256": entry.get(
                    "sha256",
                    hashlib.sha256(content).hexdigest(),
                ),
            }
        )
    report = (
        index / "github_dual_artifact_run_groups"
        / SLUG / f"{RUN_ID}.json"
    )
    report.parent.mkdir(parents=True)
    report.write_text(
        json.dumps(
            {
                "schema": (
                    "missipy.github.dual_artifact_fetch_run_group.v1"
                ),
                "status": "ready",
                "repository": REPOSITORY,
                "run_id": RUN_ID,
                "collected_files": collected,
            }
        ),
        encoding="utf-8",
    )
    return raw, index


def test_dataset_accepts_optional_advisory_absence(tmp_path) -> None:
    raw, index = _dataset(
        tmp_path,
        [_entry("request"), _entry("manifest")],
    )
    bundle = load_imported_github_run_bundle(
        dataset_raw_path=raw,
        dataset_index_path=index,
        repository=REPOSITORY,
        run_id=RUN_ID,
    )
    assert [member.filename for member in bundle.members] == [
        "authoritative_request.json",
        "dual_artifact_manifest.json",
    ]


def test_dataset_rejects_duplicate_imported_member(tmp_path) -> None:
    request = _entry("request")
    raw, index = _dataset(
        tmp_path,
        [request, dict(request), _entry("manifest")],
    )
    with pytest.raises(
        ValueError,
        match="duplicate imported member",
    ):
        load_imported_github_run_bundle(
            dataset_raw_path=raw,
            dataset_index_path=index,
            repository=REPOSITORY,
            run_id=RUN_ID,
        )


def test_dataset_rejects_sha256_mismatch(tmp_path) -> None:
    request = _entry("request")
    request["sha256"] = "0" * 64
    raw, index = _dataset(
        tmp_path,
        [request, _entry("manifest")],
    )
    with pytest.raises(ValueError, match="sha256 mismatch"):
        load_imported_github_run_bundle(
            dataset_raw_path=raw,
            dataset_index_path=index,
            repository=REPOSITORY,
            run_id=RUN_ID,
        )


def _preview() -> dict[str, object]:
    return {
        "schema": PUBLICATION_PREVIEW_SCHEMA,
        "source_candidate_ref": "github-request-0123456789abcdef",
        "advisory_context_ref": (
            "ctx:github-advisory:0123456789abcdef01234567"
        ),
        "advisory_artifact_ref": "github-advisory:abc",
        "summary": "Résumé contrôlé.",
        "suggested_route": "Audit puis validation opérateur.",
        "questions": [],
        "risks": [],
        "confidence": 0.72,
        "advisory_is_authority": False,
        "operator_decision_required": True,
        "publication_gate_required": True,
        "github_mutation_performed": False,
    }


def _publication(comments=()):
    return GitHubControlledAdvisoryIssuePublicationCommand(
        repository=REPOSITORY,
        issue_number=15,
        policy_decision_id="policy:0281:r8:closure-matrix",
        operator_decision="approve",
        publication_preview=_preview(),
        existing_comments=tuple(comments),
    )


def test_publication_create_replay_collision_matrix() -> None:
    create = plan_github_controlled_advisory_issue_publication(
        _publication()
    )
    replay = plan_github_controlled_advisory_issue_publication(
        _publication(
            (
                GitHubIssueCommentSnapshot(
                    comment_id=42,
                    body=create.body,
                ),
            )
        )
    )
    collision = plan_github_controlled_advisory_issue_publication(
        _publication(
            (
                GitHubIssueCommentSnapshot(
                    comment_id=42,
                    body=create.body + "\nchanged remotely",
                ),
            )
        )
    )

    assert create.action == "create"
    assert replay.action == "replay"
    assert replay.plan_digest == create.plan_digest
    assert collision.action == "collision"
    assert collision.valid is False
    for plan in (create, replay, collision):
        assert plan.github_mutation_allowed is False
        assert plan.github_mutation_performed is False
        assert plan.advisory_is_authority is False
