from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_workflow_uses_read_permissions_and_separate_uploads():
 t=(ROOT/"templates/github/autodoc-dual-artifact.yml").read_text()
 for m in ("contents: read","issues: read","autodoc-authoritative-request","autodoc-copilot-advisory","autodoc-dual-artifact-manifest","AUTODOC_COPILOT_ADVISORY_ENABLED"):
  assert m in t
 for bad in ("contents: write","issues: write","pull_request_target"):
  assert bad not in t
def test_copilot_is_advisory_and_tool_denied():
 t=(ROOT/"templates/github/scripts/run_autodoc_copilot_advisory.py").read_text()
 for m in ("--no-ask-user","--deny-tool=write","--deny-tool=shell","usable_as_authority\":False","Do not modify it"):
  assert m in t
 assert "COPILOT_GITHUB_TOKEN" not in t
