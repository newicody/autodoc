from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (
    ROOT
    / "templates/github/projects-repository/.github/workflows/"
    "autodoc-controlled-research.yml"
)


def test_legacy_markers_remain_without_reverting_dynamic_upload_names() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    for marker in (
        "autodoc-authoritative-request",
        "autodoc-copilot-advisory",
        "autodoc-dual-artifact-manifest",
    ):
        assert marker in text

    for output_name in (
        "request_name",
        "advisory_name",
        "manifest_name",
    ):
        assert (
            "name: ${{ steps.artifact-identity.outputs."
            f"{output_name} }}"
        ) in text

    upload_name_values = re.findall(r"^\s+name:\s+(.+)$", text, re.MULTILINE)
    assert "autodoc-authoritative-request" not in upload_name_values
    assert "autodoc-copilot-advisory" not in upload_name_values
    assert "autodoc-dual-artifact-manifest" not in upload_name_values
