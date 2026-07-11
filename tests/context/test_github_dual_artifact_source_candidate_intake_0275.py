import json
from context.github_dual_artifact_contract_0275 import *
from context.github_dual_artifact_source_candidate_intake_0275 import *
def artifacts(with_adv=True):
 r=GitHubAuthoritativeRequestArtifact("frame:1","rev:1","github-request:x","newicody/autodoc",1,"Authoritative title","Authoritative body","https://x/1"); rb=canonical_json_bytes(r.to_mapping()); a=None; ab=None
 if with_adv:
  a=GitHubCopilotAdvisoryArtifact("frame:1","rev:1","github-advisory:x",r.artifact_ref,"a"*64,"b"*64,"DO NOT COPY","route"); ab=canonical_json_bytes(a.to_mapping())
 m=build_dual_artifact_manifest(r,rb,a,ab); return rb,canonical_json_bytes(m.to_mapping()),ab
def test_candidate_uses_request_not_advisory_content():
 rb,mb,ab=artifacts(); result=run_github_dual_artifact_source_candidate_intake(rb,mb,ab)
 assert result.valid
 assert result.source_candidate["title"]=="Authoritative title" and result.source_candidate["body"]=="Authoritative body"
 assert "DO NOT COPY" not in json.dumps(result.source_candidate)
 assert result.source_candidate["metadata"]["advisory_content_copied"] is False
def test_digest_tamper_blocks_intake():
 rb,mb,ab=artifacts(); result=run_github_dual_artifact_source_candidate_intake(rb+b" ",mb,ab)
 assert not result.valid and "request digest mismatch" in result.issues
def test_advisory_can_be_absent():
 rb,mb,ab=artifacts(False); result=run_github_dual_artifact_source_candidate_intake(rb,mb)
 assert result.valid and result.advisory=={}
