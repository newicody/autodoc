from context.readable_copilot_publication_wiring_0287 import (
    build_combined_publication_plan,
    enrich_projectv2_preview,
    plan_readable_issue_publication,
    resolve_readable_copilot_publication_identity,
)


def _payloads():
    preview = {
        "schema": "missipy.github.copilot_advisory_publication_preview.v2",
        "repository": "newicody/projects",
        "issue_number": 42,
        "source_candidate_ref": "github-frame:newicody/projects/issues/42",
        "advisory_artifact_ref": "github-advisory:abc",
        "workflow_run_ref": "github-actions-run:29255262261",
    }
    identity = {
        "schema": "autodoc.human_readable_artifact_identity_bundle.v1",
        "repository": "newicody/projects",
        "issue_number": 42,
        "source_title": "Validation chaîne GitHub vers Autodoc",
        "source_ref": "github-frame:newicody/projects/issues/42",
        "workflow_run_id": "29255262261",
        "bundle_digest": "sha256:" + "a" * 64,
        "identities": [
            {
                "artifact_kind": "copilot_advisory",
                "display_title": (
                    "Premier avis Copilot — Validation chaîne GitHub vers Autodoc"
                ),
                "actions_name": (
                    "autodoc-i42-validation-chaine-github-autodoc"
                    "--copilot-advisory-v2"
                ),
                "artifact_ref": "github-advisory:abc",
            }
        ],
    }
    return preview, identity


def test_identity_correlates_readable_name_run_url_and_typed_ref() -> None:
    preview, bundle = _payloads()
    identity = resolve_readable_copilot_publication_identity(preview, bundle)
    assert identity.workflow_run_url.endswith("/actions/runs/29255262261")
    assert identity.display_title.startswith("Premier avis Copilot —")
    assert "github-advisory:abc" in identity.project_artifact_value
    assert len(identity.project_artifact_value) <= 256


def test_project_preview_keeps_technical_ref_and_writes_readable_locator() -> None:
    preview, bundle = _payloads()
    identity = resolve_readable_copilot_publication_identity(preview, bundle)
    enriched = enrich_projectv2_preview(preview, identity)
    assert enriched["technical_advisory_artifact_ref"] == "github-advisory:abc"
    assert enriched["advisory_artifact_ref"] == identity.project_artifact_value
    assert identity.workflow_run_url in enriched["advisory_artifact_ref"]


def test_issue_plan_is_readable_and_idempotent() -> None:
    preview, bundle = _payloads()
    identity = resolve_readable_copilot_publication_identity(preview, bundle)
    marker = "<!-- autodoc:copilot-advisory-v2:abc -->"
    base = {
        "valid": True,
        "action": "create",
        "issues": [],
        "marker": marker,
        "body": (
            marker
            + "\n## Autodoc — premier avis Copilot\n\n"
            + "- Avis Copilot : `github-advisory:abc`\n"
        ),
    }
    create = plan_readable_issue_publication(
        base_plan=base,
        identity=identity,
        existing_comments=(),
        policy_decision_id="policy:test",
    )
    assert create.action == "create"
    assert identity.display_title in create.body
    assert identity.actions_name in create.body
    assert identity.workflow_run_url in create.body
    replay = plan_readable_issue_publication(
        base_plan=base,
        identity=identity,
        existing_comments=({"id": 7, "body": create.body, "html_url": "u"},),
        policy_decision_id="policy:test",
    )
    assert replay.action == "replay"
    collision = plan_readable_issue_publication(
        base_plan=base,
        identity=identity,
        existing_comments=({"id": 7, "body": marker + " changed", "html_url": "u"},),
        policy_decision_id="policy:test",
    )
    assert collision.action == "collision"


def test_combined_digest_binds_both_surfaces_and_identity() -> None:
    preview, bundle = _payloads()
    identity = resolve_readable_copilot_publication_identity(preview, bundle)
    marker = "<!-- autodoc:copilot-advisory-v2:abc -->"
    issue = plan_readable_issue_publication(
        base_plan={
            "valid": True,
            "action": "create",
            "issues": [],
            "marker": marker,
            "body": marker + "\n## Autodoc — premier avis Copilot\n"
            "- Avis Copilot : `github-advisory:abc`\n",
        },
        identity=identity,
        existing_comments=(),
        policy_decision_id="policy:test",
    )
    combined = build_combined_publication_plan(
        issue_plan=issue,
        project_plan_digest="b" * 64,
        project_action="update",
        identity=identity,
        policy_decision_id="policy:test",
        project_valid=True,
    )
    assert combined.valid
    assert len(combined.plan_digest) == 64
    changed = build_combined_publication_plan(
        issue_plan=issue,
        project_plan_digest="c" * 64,
        project_action="update",
        identity=identity,
        policy_decision_id="policy:test",
        project_valid=True,
    )
    assert changed.plan_digest != combined.plan_digest
