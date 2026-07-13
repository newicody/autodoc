from __future__ import annotations

from context.github_dual_artifact_contract_0275 import (
    GitHubAuthoritativeRequestArtifact,
    GitHubCopilotAdvisoryArtifact,
    build_dual_artifact_manifest,
    canonical_json_bytes,
)
from context.github_dual_artifact_run_assembly_0281 import (
    GitHubDualArtifactRunAssemblyCommand,
    GitHubDualArtifactRunAssemblyPolicy,
    GitHubDualArtifactRunMember,
    run_github_dual_artifact_run_assembly,
)


def _members(*, with_advisory: bool = True):
    request = GitHubAuthoritativeRequestArtifact(
        origin_frame_id="github-frame:newicody/projects:15:29237396998",
        ticket_revision_id="github-ticket-revision:abc",
        artifact_ref="github-request:newicody/projects:15:abc",
        repository="newicody/projects",
        issue_number=15,
        title="Authoritative title",
        body="Authoritative body",
        issue_url="https://github.com/newicody/projects/issues/15",
    )
    request_bytes = canonical_json_bytes(request.to_mapping())
    advisory = None
    advisory_bytes = None
    if with_advisory:
        advisory = GitHubCopilotAdvisoryArtifact(
            origin_frame_id=request.origin_frame_id,
            ticket_revision_id=request.ticket_revision_id,
            artifact_ref="github-advisory:newicody/projects:15:def",
            request_artifact_ref=request.artifact_ref,
            prompt_digest="a" * 64,
            response_digest="b" * 64,
            summary="Copilot summary retained in the intake result",
            suggested_route="Inspect then promote",
            confidence=0.75,
        )
        advisory_bytes = canonical_json_bytes(advisory.to_mapping())
    manifest = build_dual_artifact_manifest(
        request,
        request_bytes,
        advisory,
        advisory_bytes,
    )
    members = [
        GitHubDualArtifactRunMember(
            "autodoc-authoritative-request",
            "authoritative_request.json",
            request_bytes,
        ),
        GitHubDualArtifactRunMember(
            "autodoc-dual-artifact-manifest",
            "dual_artifact_manifest.json",
            canonical_json_bytes(manifest.to_mapping()),
        ),
    ]
    if advisory_bytes is not None:
        members.append(
            GitHubDualArtifactRunMember(
                "autodoc-copilot-advisory",
                "copilot_advisory.json",
                advisory_bytes,
            )
        )
    return tuple(members)


def _command(members):
    return GitHubDualArtifactRunAssemblyCommand(
        repository="newicody/projects",
        run_id="29237396998",
        members=tuple(members),
    )


def test_assembly_reuses_0275_intake_and_retains_full_advisory() -> None:
    result = run_github_dual_artifact_run_assembly(_command(_members()))

    assert result.valid
    assert result.advisory_present
    assert result.advisory_payload_retained
    assert result.intake["advisory"]["summary"].startswith("Copilot summary")
    assert result.intake["source_candidate"]["title"] == "Authoritative title"
    assert result.intake["source_candidate"]["body"] == "Authoritative body"
    assert result.advisory_content_authoritative is False
    assert result.github_mutation_performed is False


def test_assembly_accepts_missing_advisory_when_manifest_does_not_require_it() -> None:
    result = run_github_dual_artifact_run_assembly(_command(_members(with_advisory=False)))

    assert result.valid
    assert not result.advisory_present
    assert result.intake["advisory"] == {}


def test_assembly_rejects_duplicate_request_members() -> None:
    members = list(_members())
    members.append(members[0])

    result = run_github_dual_artifact_run_assembly(_command(members))

    assert not result.valid
    assert "duplicate request artifact member" in result.issues
    assert result.intake == {}


def test_assembly_rejects_digest_mismatch_through_existing_intake() -> None:
    members = list(_members())
    request = members[0]
    members[0] = GitHubDualArtifactRunMember(
        request.artifact_name,
        request.filename,
        request.content + b" ",
    )

    result = run_github_dual_artifact_run_assembly(_command(members))

    assert not result.valid
    assert "request digest mismatch" in result.issues


def test_assembly_ignores_unrecognized_artifacts_by_default() -> None:
    members = (*_members(), GitHubDualArtifactRunMember("autodoc-extra", "extra.json", b"{}"))

    result = run_github_dual_artifact_run_assembly(_command(members))

    assert result.valid
    assert result.ignored_member_count == 1
    assert result.recognized_member_count == 3


def test_policy_can_require_advisory_and_command_cannot_execute() -> None:
    result = run_github_dual_artifact_run_assembly(
        _command(_members(with_advisory=False)),
        GitHubDualArtifactRunAssemblyPolicy(allow_missing_advisory=False),
    )
    assert not result.valid
    assert "Copilot advisory artifact member is required" in result.issues

    try:
        GitHubDualArtifactRunAssemblyCommand(
            repository="newicody/projects",
            run_id="1",
            members=(),
            execute=True,
        )
    except ValueError as exc:
        assert "read-only" in str(exc)
    else:
        raise AssertionError("execute=True must be rejected")
