from __future__ import annotations

import json

import pytest

from context.github_dual_artifact_contract_0275 import (
    ADVISORY_SCHEMA_V1,
    ADVISORY_SCHEMA_V2,
    GitHubAuthoritativeRequestArtifact,
    GitHubCopilotAdvisoryArtifact,
    GitHubCopilotFirstOpinionAdvisoryArtifact,
    GitHubDualArtifactContractError,
    build_dual_artifact_manifest,
    canonical_json_bytes,
    parse_copilot_advisory_artifact,
)
from context.github_dual_artifact_source_candidate_intake_0275 import (
    run_github_dual_artifact_source_candidate_intake,
)


def _request() -> GitHubAuthoritativeRequestArtifact:
    return GitHubAuthoritativeRequestArtifact(
        origin_frame_id="frame:0287-r7-r3",
        ticket_revision_id="revision:42",
        artifact_ref="github-request:newicody/projects:42",
        repository="newicody/projects",
        issue_number=42,
        title="Authoritative title",
        body="Authoritative body",
        issue_url="https://github.com/newicody/projects/issues/42",
        labels=("research",),
    )


def _v1(request: GitHubAuthoritativeRequestArtifact):
    return GitHubCopilotAdvisoryArtifact(
        origin_frame_id=request.origin_frame_id,
        ticket_revision_id=request.ticket_revision_id,
        artifact_ref="github-advisory:v1:42",
        request_artifact_ref=request.artifact_ref,
        prompt_digest="a" * 64,
        response_digest="b" * 64,
        summary="Historical summary",
        suggested_route="review",
        risks=("historical-risk",),
        confidence=0.5,
    )


def _v2(request: GitHubAuthoritativeRequestArtifact):
    return GitHubCopilotFirstOpinionAdvisoryArtifact(
        origin_frame_id=request.origin_frame_id,
        ticket_revision_id=request.ticket_revision_id,
        artifact_ref="github-advisory:v2:42",
        request_artifact_ref=request.artifact_ref,
        prompt_digest="c" * 64,
        response_digest="d" * 64,
        concrete_objective="DO NOT COPY objective into the request",
        expected_result="A correlated v2 advisory remains consultative.",
        provided_constraints=("No new Scheduler.",),
        success_criteria=("The intake validates both public schemas.",),
    )


def _intake(advisory):
    request = _request()
    request_bytes = canonical_json_bytes(request.to_mapping())
    advisory_bytes = canonical_json_bytes(advisory.to_mapping())
    manifest = build_dual_artifact_manifest(
        request,
        request_bytes,
        advisory,
        advisory_bytes,
    )
    result = run_github_dual_artifact_source_candidate_intake(
        request_bytes,
        canonical_json_bytes(manifest.to_mapping()),
        advisory_bytes,
    )
    return result


def test_dispatcher_keeps_v1_and_v2_as_distinct_public_contracts() -> None:
    request = _request()
    v1 = parse_copilot_advisory_artifact(_v1(request).to_mapping())
    v2 = parse_copilot_advisory_artifact(_v2(request).to_mapping())

    assert v1.schema == ADVISORY_SCHEMA_V1
    assert v1.summary == "Historical summary"
    assert not hasattr(v1, "concrete_objective")
    assert v2.schema == ADVISORY_SCHEMA_V2
    assert v2.concrete_objective.startswith("DO NOT COPY")
    assert not hasattr(v2, "summary")


def test_v2_contract_is_strict_and_cannot_embed_v1_analysis_fields() -> None:
    mapping = _v2(_request()).to_mapping()
    mapping["summary"] = "silent reinterpretation"

    with pytest.raises(GitHubDualArtifactContractError, match="field mismatch"):
        parse_copilot_advisory_artifact(mapping)

    mapping = _v2(_request()).to_mapping()
    mapping["success_criteria"] = []
    with pytest.raises(GitHubDualArtifactContractError, match="must not be empty"):
        parse_copilot_advisory_artifact(mapping)

    mapping = _v2(_request()).to_mapping()
    mapping["provided_constraints"] = "not-an-array"
    with pytest.raises(GitHubDualArtifactContractError, match="must be an array"):
        parse_copilot_advisory_artifact(mapping)

    mapping = _v2(_request()).to_mapping()
    mapping["usable_as_hint"] = 1
    with pytest.raises(GitHubDualArtifactContractError, match="flags are locked"):
        parse_copilot_advisory_artifact(mapping)


def test_intake_accepts_v1_without_copying_advisory_content() -> None:
    result = _intake(_v1(_request()))

    assert result.valid
    assert result.advisory["schema"] == ADVISORY_SCHEMA_V1
    assert result.source_candidate["title"] == "Authoritative title"
    assert result.source_candidate["metadata"]["advisory_schema"] == ADVISORY_SCHEMA_V1
    assert result.source_candidate["metadata"]["advisory_content_copied"] is False


def test_intake_accepts_v2_without_copying_first_opinion_content() -> None:
    result = _intake(_v2(_request()))

    assert result.valid
    assert result.advisory["schema"] == ADVISORY_SCHEMA_V2
    assert result.advisory["success_criteria"] == [
        "The intake validates both public schemas."
    ]
    candidate = json.dumps(result.source_candidate, sort_keys=True)
    assert "DO NOT COPY objective" not in candidate
    assert result.source_candidate["metadata"]["advisory_schema"] == ADVISORY_SCHEMA_V2
    assert result.source_candidate["metadata"]["advisory_content_copied"] is False


def test_unknown_advisory_schema_fails_closed() -> None:
    mapping = _v2(_request()).to_mapping()
    mapping["schema"] = "missipy.github.copilot_advisory.v3"

    with pytest.raises(GitHubDualArtifactContractError, match="unsupported"):
        parse_copilot_advisory_artifact(mapping)


def test_run_assembly_reuses_intake_for_v2_without_module_change() -> None:
    from context.github_dual_artifact_run_assembly_0281 import (
        GitHubDualArtifactRunAssemblyCommand,
        GitHubDualArtifactRunMember,
        run_github_dual_artifact_run_assembly,
    )

    request = _request()
    advisory = _v2(request)
    request_bytes = canonical_json_bytes(request.to_mapping())
    advisory_bytes = canonical_json_bytes(advisory.to_mapping())
    manifest = build_dual_artifact_manifest(
        request,
        request_bytes,
        advisory,
        advisory_bytes,
    )
    members = (
        GitHubDualArtifactRunMember(
            "autodoc-authoritative-request",
            "authoritative_request.json",
            request_bytes,
        ),
        GitHubDualArtifactRunMember(
            "autodoc-copilot-advisory",
            "copilot_advisory.json",
            advisory_bytes,
        ),
        GitHubDualArtifactRunMember(
            "autodoc-dual-artifact-manifest",
            "dual_artifact_manifest.json",
            canonical_json_bytes(manifest.to_mapping()),
        ),
    )

    result = run_github_dual_artifact_run_assembly(
        GitHubDualArtifactRunAssemblyCommand(
            repository="newicody/projects",
            run_id="28773",
            members=members,
        )
    )

    assert result.valid
    assert result.intake["advisory"]["schema"] == ADVISORY_SCHEMA_V2
    assert result.intake["source_candidate"]["title"] == "Authoritative title"
    assert result.advisory_content_authoritative is False
    assert result.github_mutation_performed is False
