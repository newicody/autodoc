"""Read-only intake of authoritative request plus optional advisory."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Any
import json
from context.github_dual_artifact_contract_0275 import GitHubAuthoritativeRequestArtifact,GitHubCopilotAdvisoryArtifact,GitHubDualArtifactManifest,sha256_bytes,validate_dual_artifact_correlation
from context.github_dual_artifact_contract_0275 import parse_copilot_advisory_artifact
from context.source_candidate import SourceCandidateInput,SourceCandidateOrigin,SourceCandidatePolicy,build_source_candidate

INTAKE_SCHEMA="missipy.github.dual_artifact_source_candidate_intake.v1"
@dataclass(frozen=True,slots=True)
class GitHubDualArtifactIntakeCommand:
 allow_missing_advisory:bool=True
 policy_decision_id:str=""
 execute:bool=False
 def __post_init__(self):
  if self.execute: raise ValueError("intake is read-only and execute must remain false")
@dataclass(frozen=True,slots=True)
class GitHubDualArtifactIntakeResult:
 valid:bool; issues:tuple[str,...]; request:Mapping[str,Any]=field(default_factory=dict); advisory:Mapping[str,Any]=field(default_factory=dict); manifest:Mapping[str,Any]=field(default_factory=dict); source_candidate:Mapping[str,Any]=field(default_factory=dict)
 request_authoritative:bool=True; advisory_used_as_hint_only:bool=True; scheduler_route_created:bool=False; sql_write_performed:bool=False; qdrant_write_performed:bool=False; github_mutation_performed:bool=False
 def to_mapping(self): return {"schema":INTAKE_SCHEMA,"valid":self.valid,"issues":list(self.issues),"request":dict(self.request),"advisory":dict(self.advisory),"manifest":dict(self.manifest),"source_candidate":dict(self.source_candidate),"request_authoritative":True,"advisory_used_as_hint_only":True,"scheduler_route_created":False,"sql_write_performed":False,"qdrant_write_performed":False,"github_mutation_performed":False}

def run_github_dual_artifact_source_candidate_intake(request_bytes:bytes,manifest_bytes:bytes,advisory_bytes:bytes|None=None,*,command=None):
 cmd=command or GitHubDualArtifactIntakeCommand(); issues=[]
 try:
  req=GitHubAuthoritativeRequestArtifact.from_mapping(json.loads(request_bytes))
  man=GitHubDualArtifactManifest.from_mapping(json.loads(manifest_bytes))
  adv=(
   None
   if advisory_bytes is None
   else parse_copilot_advisory_artifact(json.loads(advisory_bytes))
  )
 except Exception as e: return GitHubDualArtifactIntakeResult(False,(str(e),))
 if man.request_sha256!=sha256_bytes(request_bytes): issues.append("request digest mismatch")
 if advisory_bytes is None:
  if man.advisory_artifact_ref is not None: issues.append("manifest requires advisory bytes")
  if not cmd.allow_missing_advisory: issues.append("advisory is required by intake command")
 else:
  if man.advisory_sha256!=sha256_bytes(advisory_bytes): issues.append("advisory digest mismatch")
 issues.extend(validate_dual_artifact_correlation(req,man,adv))
 if issues: return GitHubDualArtifactIntakeResult(False,tuple(dict.fromkeys(issues)),req.to_mapping(),{} if adv is None else adv.to_mapping(),man.to_mapping())
 metadata={"request_artifact_ref":req.artifact_ref,"ticket_revision_id":req.ticket_revision_id,"origin_frame_id":req.origin_frame_id,"advisory_present":adv is not None,"advisory_ref":"" if adv is None else adv.artifact_ref,"advisory_response_digest":"" if adv is None else adv.response_digest,"advisory_content_copied":False,"request_authoritative":True}
 metadata["advisory_schema"]="" if adv is None else adv.schema
 created=build_source_candidate(SourceCandidateInput(title=req.title,body=req.body,origin=SourceCandidateOrigin(kind="github",reference=req.artifact_ref,repository=req.repository),labels=tuple(dict.fromkeys(("github-request",*req.labels))),metadata=metadata),SourceCandidatePolicy(default_repository=req.repository,id_prefix="github-request"))
 return GitHubDualArtifactIntakeResult(True,(),req.to_mapping(),{} if adv is None else adv.to_mapping(),man.to_mapping(),created.candidate.to_json_dict())
