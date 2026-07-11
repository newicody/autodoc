import json, pytest, dataclasses
from context.github_dual_artifact_contract_0275 import *
def request(): return GitHubAuthoritativeRequestArtifact("frame:1","revision:1","github-request:test","newicody/autodoc",42,"Title","Body","https://github.com/newicody/autodoc/issues/42",("feature",))
def advisory(req=None):
 req=req or request(); d="a"*64
 return GitHubCopilotAdvisoryArtifact(req.origin_frame_id,req.ticket_revision_id,"github-advisory:test",req.artifact_ref,d,d,"Summary","laboratory",("assumption",),("question",),("risk",),0.5)
def test_manifest_keeps_physical_separation_and_serializes():
 r=request(); rb=canonical_json_bytes(r.to_mapping()); a=advisory(r); ab=canonical_json_bytes(a.to_mapping()); m=build_dual_artifact_manifest(r,rb,a,ab)
 assert m.request_is_authority and not m.advisory_is_authority
 assert m.request_filename!=m.advisory_filename
 assert validate_dual_artifact_correlation(r,m,a)==()
 json.dumps(m.to_mapping())
def test_advisory_can_never_be_authority():
 with pytest.raises(GitHubDualArtifactContractError):
  GitHubCopilotAdvisoryArtifact("frame:1","revision:1","github-advisory:x","github-request:x","a"*64,"b"*64,"s","r",usable_as_authority=True)
def test_request_rejects_embedded_advisory():
 with pytest.raises(GitHubDualArtifactContractError):
  GitHubAuthoritativeRequestArtifact("f","r","github-request:x","o/r",1,"t","b","https://x",advisory_content_embedded=True)
def test_correlation_mismatch_is_rejected():
 r=request(); a=advisory(r); bad=dataclasses.replace(a,ticket_revision_id="revision:2")
 with pytest.raises(GitHubDualArtifactContractError): build_dual_artifact_manifest(r,canonical_json_bytes(r.to_mapping()),bad,canonical_json_bytes(bad.to_mapping()))
