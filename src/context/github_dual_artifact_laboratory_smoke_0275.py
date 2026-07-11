"""Compose dual-artifact intake with the existing 0274 laboratory smoke."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Any
from context.github_dual_artifact_source_candidate_intake_0275 import GitHubDualArtifactIntakeCommand,run_github_dual_artifact_source_candidate_intake
from context.source_candidate import SourceCandidate,SourceCandidateDecision,SourceCandidateOrigin,apply_source_candidate_decision
from context.fake_laboratory_existing_scheduler_closed_loop_smoke_0274 import FakeLaboratoryClosedLoopSmokeCommand,run_fake_laboratory_existing_scheduler_closed_loop_smoke

SCHEMA="missipy.github.dual_artifact_laboratory_smoke.v1"
@dataclass(frozen=True,slots=True)
class GitHubDualArtifactLaboratorySmokeCommand:
 decision:SourceCandidateDecision
 laboratory:FakeLaboratoryClosedLoopSmokeCommand
 policy_decision_id:str
 def __post_init__(self):
  if self.decision.action not in {"promote","merge"}: raise ValueError("laboratory smoke requires promote or merge")
  if not self.policy_decision_id.strip(): raise ValueError("policy_decision_id is required")
@dataclass(frozen=True,slots=True)
class GitHubDualArtifactLaboratorySmokeResult:
 valid:bool; issues:tuple[str,...]; intake:Mapping[str,Any]=field(default_factory=dict); approved_candidate:Mapping[str,Any]=field(default_factory=dict); laboratory:Mapping[str,Any]=field(default_factory=dict); publication_preview:Mapping[str,Any]=field(default_factory=dict)
 github_mutation_performed:bool=False; scheduler_created:bool=False; parallel_orchestrator_created:bool=False
 def to_mapping(self): return {"schema":SCHEMA,"valid":self.valid,"issues":list(self.issues),"intake":dict(self.intake),"approved_candidate":dict(self.approved_candidate),"laboratory":dict(self.laboratory),"publication_preview":dict(self.publication_preview),"github_mutation_performed":False,"scheduler_created":False,"parallel_orchestrator_created":False,"publication_gate_required":True}
async def run_github_dual_artifact_laboratory_smoke(scheduler,request_bytes,manifest_bytes,advisory_bytes,command,**laboratory_dependencies):
 intake=run_github_dual_artifact_source_candidate_intake(request_bytes,manifest_bytes,advisory_bytes,command=GitHubDualArtifactIntakeCommand())
 if not intake.valid: return GitHubDualArtifactLaboratorySmokeResult(False,intake.issues,intake.to_mapping())
 c=intake.source_candidate; candidate=SourceCandidate(candidate_id=c["candidate_id"],title=c["title"],body=c["body"],origin=SourceCandidateOrigin(**c["origin"]),status=c["status"],labels=tuple(c["labels"]),metadata=c["metadata"])
 approved=apply_source_candidate_decision(candidate,command.decision)
 result=await run_fake_laboratory_existing_scheduler_closed_loop_smoke(scheduler,command.laboratory,**laboratory_dependencies)
 mapping=result.to_mapping(); issues=[]
 if not result.valid: issues.extend(getattr(result,"issues",("laboratory smoke invalid",)))
 if getattr(result,"github_mutation_performed",False): issues.append("laboratory path mutated GitHub")
 preview={"schema":"missipy.github.publication_preview.v1","source_candidate_ref":approved.candidate_id,"source_sql_ref":getattr(result,"sql_ref",""),"source_final_ref":getattr(result,"final_ref",""),"status":"pending","publication_gate_required":True,"github_mutation_performed":False}
 return GitHubDualArtifactLaboratorySmokeResult(not issues,tuple(issues),intake.to_mapping(),approved.to_json_dict(),mapping,preview)
