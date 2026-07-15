from __future__ import annotations

from copy import deepcopy

from context.correlated_research_work_package_0287 import (
    CorrelatedResearchWorkPackageCommand,
    build_correlated_research_work_package,
)


REQUEST_SHA = "1" * 64
ADVISORY_SHA = "2" * 64
ATTACHMENT_SHA = "3" * 64


def _run_assembly(*, advisory: bool = True) -> dict[str, object]:
    request = {
        "schema": "missipy.github.authoritative_request.v1",
        "origin_frame_id": "github-frame:newicody/projects/issues/17",
        "ticket_revision_id": "github-ticket-revision:rev-17",
        "artifact_ref": "github-request:req-17",
        "repository": "newicody/projects",
        "issue_number": 17,
        "title": "Étudier différentes dimensions de l'amour",
        "body": "Comparer affection, réciprocité et dynamique relationnelle.",
        "issue_url": "https://github.com/newicody/projects/issues/17",
        "labels": ["research"],
        "actor": "eric",
        "event_name": "issues",
        "metadata": {},
        "authoritative": True,
        "advisory_content_embedded": False,
        "remote_mutation_requested": False,
    }
    advisory_payload: dict[str, object] = {}
    if advisory:
        advisory_payload = {
            "schema": "missipy.github.copilot_advisory.v2",
            "origin_frame_id": request["origin_frame_id"],
            "ticket_revision_id": request["ticket_revision_id"],
            "artifact_ref": "github-advisory:adv-17",
            "request_artifact_ref": request["artifact_ref"],
            "prompt_digest": "4" * 64,
            "response_digest": "5" * 64,
            "concrete_objective": "Analyser les dimensions exprimées.",
            "expected_result": "Deux analyses spécialisées puis une synthèse.",
            "provided_constraints": ["Rester fondé sur les éléments fournis."],
            "success_criteria": ["Conserver les incertitudes."],
            "producer_kind": "github_copilot_cli",
            "trusted": False,
            "usable_as_hint": True,
            "usable_as_authority": False,
        }
    manifest = {
        "schema": "missipy.github.dual_artifact_manifest.v1",
        "manifest_ref": "github-dual-manifest:manifest-17",
        "origin_frame_id": request["origin_frame_id"],
        "ticket_revision_id": request["ticket_revision_id"],
        "request_artifact_ref": request["artifact_ref"],
        "request_filename": "authoritative_request.json",
        "request_sha256": REQUEST_SHA,
        "advisory_artifact_ref": (
            advisory_payload.get("artifact_ref") if advisory else None
        ),
        "advisory_filename": "copilot_advisory.json" if advisory else None,
        "advisory_sha256": ADVISORY_SHA if advisory else None,
        "request_is_authority": True,
        "advisory_is_authority": False,
    }
    intake = {
        "schema": "missipy.github.dual_artifact_source_candidate_intake.v1",
        "valid": True,
        "issues": [],
        "request": request,
        "advisory": advisory_payload,
        "manifest": manifest,
        "source_candidate": {
            "schema": "missipy.source_candidate.v1",
            "candidate_id": "github-request-candidate-17",
            "title": request["title"],
            "body": request["body"],
            "origin": {
                "kind": "github",
                "reference": request["artifact_ref"],
                "repository": request["repository"],
            },
            "status": "new",
            "terminal": False,
            "actionable": True,
            "labels": ["github-request", "research"],
            "metadata": {},
            "decision": None,
        },
        "request_authoritative": True,
        "advisory_used_as_hint_only": True,
        "scheduler_route_created": False,
        "sql_write_performed": False,
        "qdrant_write_performed": False,
        "github_mutation_performed": False,
    }
    return {
        "schema": "missipy.github.dual_artifact_run_assembly.v1",
        "valid": True,
        "issues": [],
        "repository": request["repository"],
        "run_id": "9001",
        "member_count": 3 if advisory else 2,
        "recognized_member_count": 3 if advisory else 2,
        "ignored_member_count": 0,
        "advisory_present": advisory,
        "request_member": {},
        "advisory_member": {},
        "manifest_member": {},
        "intake": intake,
        "advisory_payload_retained": advisory,
        "advisory_content_authoritative": False,
        "filesystem_write_performed": False,
        "scheduler_route_created": False,
        "sql_write_performed": False,
        "qdrant_write_performed": False,
        "github_mutation_performed": False,
    }


def _attachment_manifest() -> dict[str, object]:
    return {
        "schema": "missipy.github_issue.attachment_manifest.v1",
        "repository": "newicody/projects",
        "issue": {
            "number": 17,
            "url": "https://github.com/newicody/projects/issues/17",
        },
        "origin_frame_id": "github-frame:newicody/projects/issues/17",
        "ticket_revision_id": "github-ticket-revision:rev-17",
        "attachments": [
            {
                "schema": "missipy.github_issue.attachment_reference.v1",
                "url": "https://github.com/user-attachments/files/love-notes.txt",
                "filename": "love-notes.txt",
                "kind": "text",
                "source": "github_issue_attachment_reference",
                "label": "notes",
                "raw_text": "[notes](...)",
                "processed": False,
            }
        ],
        "counts": {"attachment_count": 1},
    }


def _fetch_report() -> dict[str, object]:
    return {
        "schema": "missipy.github_attachment.reference_fetch_report.v1",
        "status": "completed",
        "repository": "newicody/projects",
        "run_id": "9001",
        "artifact_id": "artifact-attachments-17",
        "origin_frame_id": "github-frame:newicody/projects/issues/17",
        "ticket_revision_id": "github-ticket-revision:rev-17",
        "counts": {
            "reference_count": 1,
            "fetched_count": 1,
            "queued_count": 1,
            "failed_count": 0,
        },
        "records": [
            {
                "schema": "missipy.github_attachment.reference_fetch_record.v1",
                "reference": {
                    "schema": "missipy.github_attachment.reference.v1",
                    "url": (
                        "https://github.com/user-attachments/files/"
                        "love-notes.txt"
                    ),
                    "filename": "love-notes.txt",
                    "kind": "text",
                    "source": "github_issue_attachment_reference",
                    "content_type": "text/plain",
                    "expected_sha256": ATTACHMENT_SHA,
                    "metadata": {},
                },
                "repository": "newicody/projects",
                "run_id": "9001",
                "artifact_id": "artifact-attachments-17",
                "origin_frame_id": "github-frame:newicody/projects/issues/17",
                "ticket_revision_id": "github-ticket-revision:rev-17",
                "raw_dataset_ref": "dataset:github-attachment:love-notes",
                "local_path": "/srv/autodoc/raw/love-notes.txt",
                "sha256": ATTACHMENT_SHA,
                "byte_count": 321,
                "status": "fetched",
                "message": "",
            }
        ],
        "queue_records": [],
        "vispy_event_path": "",
    }


def _command(**overrides: object) -> CorrelatedResearchWorkPackageCommand:
    values: dict[str, object] = {
        "run_assembly": _run_assembly(),
        "attachment_manifest": _attachment_manifest(),
        "attachment_fetch_report": _fetch_report(),
        "conversation_ref": "conversation:love-study:17",
        "return_route_ref": "return-route:github-issue:17",
        "context_generation": 3,
        "context_refs": ("context:operator-approved:17",),
        "evidence_refs": ("evidence:issue-body:17",),
    }
    values.update(overrides)
    return CorrelatedResearchWorkPackageCommand(**values)


def test_builds_deterministic_correlated_work_package() -> None:
    first = build_correlated_research_work_package(_command())
    second = build_correlated_research_work_package(_command())

    assert first.valid is True
    assert first.issues == ()
    assert first.work_package == second.work_package
    package = first.work_package
    assert package["schema"] == "missipy.research.correlated_work_package.v1"
    assert str(package["work_package_ref"]).startswith("research-work-package:")
    assert package["request_authoritative"] is True
    assert package["advisory_used_as_hint_only"] is True
    assert package["ready_for_laboratory_route"] is True
    assert package["scheduler_route_created"] is False
    assert package["authoritative_request"]["body"].startswith("Comparer")
    assert package["copilot_advisory"]["schema"].endswith("advisory.v2")
    assert package["attachment_refs"] == [
        "dataset:github-attachment:love-notes"
    ]
    attachment = package["attachments"][0]
    assert attachment["sha256"] == ATTACHMENT_SHA
    assert attachment["raw_bytes_embedded"] is False
    assert attachment["local_path_exposed"] is False
    assert "local_path" not in attachment


def test_rejects_run_authority_or_mutation_boundary_drift() -> None:
    run = _run_assembly()
    run["github_mutation_performed"] = True
    result = build_correlated_research_work_package(
        _command(run_assembly=run)
    )

    assert result.valid is False
    assert "github_mutation_performed must be False" in result.issues
    assert result.work_package == {}


def test_rejects_request_and_attachment_correlation_mismatch() -> None:
    attachment_manifest = _attachment_manifest()
    attachment_manifest["ticket_revision_id"] = "github-ticket-revision:other"
    result = build_correlated_research_work_package(
        _command(attachment_manifest=attachment_manifest)
    )

    assert result.valid is False
    assert "attachment ticket_revision_id mismatch" in result.issues


def test_referenced_attachment_must_have_completed_fetch() -> None:
    result = build_correlated_research_work_package(
        _command(attachment_fetch_report={})
    )

    assert result.valid is False
    assert "referenced attachments require a fetch report" in result.issues


def test_fetch_report_cannot_smuggle_unlisted_attachment() -> None:
    report = _fetch_report()
    extra = deepcopy(report["records"][0])
    extra["reference"]["url"] = (
        "https://github.com/user-attachments/files/extra.txt"
    )
    extra["raw_dataset_ref"] = "dataset:github-attachment:extra"
    extra["sha256"] = "6" * 64
    extra["reference"]["expected_sha256"] = "6" * 64
    report["records"].append(extra)
    result = build_correlated_research_work_package(
        _command(attachment_fetch_report=report)
    )

    assert result.valid is False
    assert any(
        issue.startswith("fetch report contains attachments absent from manifest")
        for issue in result.issues
    )


def test_missing_advisory_can_be_explicitly_allowed() -> None:
    result = build_correlated_research_work_package(
        _command(
            run_assembly=_run_assembly(advisory=False),
            require_advisory=False,
        )
    )

    assert result.valid is True
    assert result.work_package["advisory_present"] is False
    assert result.work_package["copilot_advisory"] == {}


def test_missing_advisory_fails_closed_when_required() -> None:
    result = build_correlated_research_work_package(
        _command(run_assembly=_run_assembly(advisory=False))
    )

    assert result.valid is False
    assert "Copilot advisory is required by work-package command" in result.issues


def test_command_is_read_only_and_rejects_string_reference_collections() -> None:
    try:
        _command(execute=True)
    except ValueError as exc:
        assert "execute must remain false" in str(exc)
    else:
        raise AssertionError("execute=True must fail")

    try:
        _command(context_refs="context:not-a-sequence")
    except ValueError as exc:
        assert "sequence of strings" in str(exc)
    else:
        raise AssertionError("string context_refs must fail")
