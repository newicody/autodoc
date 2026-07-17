from context.human_readable_artifact_identity_0287 import (
    build_human_readable_artifact_identity_bundle,
    matches_actions_artifact_name,
    slugify_issue_title,
)


def _payloads():
    issue = {"number": 42, "title": "Validation chaîne GitHub → Autodoc"}
    request = {
        "repository": "newicody/projects",
        "issue_number": 42,
        "title": issue["title"],
        "artifact_ref": "github-request:req1",
    }
    advisory = {
        "artifact_ref": "github-advisory:adv1",
        "request_artifact_ref": request["artifact_ref"],
    }
    manifest = {
        "manifest_ref": "github-dual-manifest:man1",
        "request_artifact_ref": request["artifact_ref"],
        "advisory_artifact_ref": advisory["artifact_ref"],
    }
    return issue, request, advisory, manifest


def test_slug_is_ascii_bounded_and_deterministic() -> None:
    assert slugify_issue_title(
        "Étude très précise : GitHub / Autodoc", issue_number=7
    ) == "etude-tres-precise-github-autodoc"
    assert slugify_issue_title("🔥", issue_number=7) == "issue-7"


def test_bundle_names_explain_issue_and_content() -> None:
    issue, request, advisory, manifest = _payloads()
    bundle = build_human_readable_artifact_identity_bundle(
        repository="newicody/projects",
        workflow_run_id="29255262261",
        issue=issue,
        request=request,
        advisory=advisory,
        manifest=manifest,
    )
    request_identity = bundle.identity("authoritative_request")
    advisory_identity = bundle.identity("copilot_advisory")
    manifest_identity = bundle.identity("run_manifest")
    assert request_identity.actions_name == (
        "autodoc-i42-validation-chaine-github-autodoc--authoritative-request-v1"
    )
    assert advisory_identity.actions_name.endswith("--copilot-advisory-v2")
    assert manifest_identity.actions_name.endswith("--run-manifest-v1")
    assert advisory_identity.display_title.startswith("Premier avis Copilot —")
    assert "concrete_objective" in advisory_identity.content_sections
    assert bundle.source_ref == "github-frame:newicody/projects/issues/42"
    assert bundle.bundle_digest.startswith("sha256:")


def test_bundle_keeps_legacy_names_for_old_run_compatibility() -> None:
    issue, request, advisory, manifest = _payloads()
    bundle = build_human_readable_artifact_identity_bundle(
        repository="newicody/projects",
        workflow_run_id="1",
        issue=issue,
        request=request,
        advisory=advisory,
        manifest=manifest,
    )
    assert bundle.identity("authoritative_request").legacy_actions_name == (
        "autodoc-authoritative-request"
    )
    assert bundle.identity("copilot_advisory").legacy_actions_name == (
        "autodoc-copilot-advisory"
    )


def test_name_matcher_accepts_old_and_new_but_not_ambiguous_shapes() -> None:
    legacy = "autodoc-copilot-advisory"
    assert matches_actions_artifact_name(legacy, legacy)
    assert matches_actions_artifact_name(
        "autodoc-i42-analyse-du-moteur--copilot-advisory-v2", legacy
    )
    assert not matches_actions_artifact_name(
        "other-i42-analyse-du-moteur--copilot-advisory-v2", legacy
    )
    assert not matches_actions_artifact_name("autodoc-copilot-advisory-copy", legacy)


def test_bundle_without_optional_advisory_keeps_request_and_manifest() -> None:
    issue, request, _advisory, manifest = _payloads()
    manifest = {
        **manifest,
        "advisory_artifact_ref": None,
    }
    bundle = build_human_readable_artifact_identity_bundle(
        repository="newicody/projects",
        workflow_run_id="2",
        issue=issue,
        request=request,
        advisory=None,
        manifest=manifest,
    )
    assert tuple(item.artifact_kind for item in bundle.identities) == (
        "authoritative_request",
        "run_manifest",
    )
