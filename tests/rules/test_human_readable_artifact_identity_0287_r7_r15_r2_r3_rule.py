from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOMAIN = ROOT / "src/context/human_readable_artifact_identity_0287.py"
TOOL = (
    ROOT
    / "templates/github/projects-repository/scripts"
    / "build_human_readable_artifact_identity.py"
)
WORKFLOW = (
    ROOT
    / "templates/github/projects-repository/.github/workflows"
    / "autodoc-controlled-research.yml"
)
CONSUMER = ROOT / "tools/run_love_actions_closed_loop_0287.py"


def test_contract_is_pure_and_keeps_immutable_refs() -> None:
    source = DOMAIN.read_text(encoding="utf-8")
    assert "HumanReadableArtifactIdentity" in source
    assert "artifact_ref" in source
    assert "bundle_digest" in source
    assert "subprocess" not in source
    assert "requests" not in source


def test_workflow_uses_readable_names_and_keeps_identity_with_manifest() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "Build human-readable artifact identities" in source
    assert "steps.artifact-identity.outputs.request_name" in source
    assert "steps.artifact-identity.outputs.advisory_name" in source
    assert "steps.artifact-identity.outputs.manifest_name" in source
    assert "out/artifact_identity.json" in source


def test_consumer_accepts_legacy_and_readable_suffixes() -> None:
    source = CONSUMER.read_text(encoding="utf-8")
    assert "matches_actions_artifact_name" in source
    assert "actual_artifact_name" in source
    domain = DOMAIN.read_text(encoding="utf-8")
    assert '"authoritative-request-v1"' in domain
    assert '"copilot-advisory-v2"' in domain
    assert '"run-manifest-v1"' in domain
