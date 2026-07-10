"""GitHub scan-once handoff from the closed Scheduler-managed frame.

0267 prepares a local handoff artifact that can later be reviewed by a GitHub
workflow surface.  It does not call the GitHub API, does not mutate issues,
projects, branches or commits, and does not start external services.

Boundary:
- local/server remains the authority.
- GitHub is a review/workflow surface, not the authority.
- scan-once means one local artifact envelope, no polling loop.
- remote mutation is forbidden in 0267.
- Scheduler.run is not modified.
- No RuntimeManager is introduced.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import hashlib, json
from pathlib import Path
from typing import Any, Mapping

HANDOFF_SCHEMA='missipy.github_scan_once_handoff.v1'
DEFAULT_REPOSITORY='newicody/autodoc'

@dataclass(frozen=True)
class GitHubScanOnceHandoffRequest:
    repository: str = DEFAULT_REPOSITORY
    operator_intent: str = 'review_closed_result_frame'
    target_surface: str = 'github_project_review'
    policy_decision_id: str = ''
    allow_remote_mutation: bool = False
    def to_mapping(self)->dict[str,Any]:
        return {'repository':self.repository,'operator_intent':self.operator_intent,'target_surface':self.target_surface,'policy_decision_id':self.policy_decision_id,'allow_remote_mutation':self.allow_remote_mutation}

@dataclass(frozen=True)
class GitHubScanOnceHandoff:
    valid: bool
    issues: tuple[str,...]
    request: GitHubScanOnceHandoffRequest
    handoff_ref: str=''
    sql_ref: str=''
    embedding_ref: str=''
    source_reports: Mapping[str,str]=field(default_factory=dict)
    summary: Mapping[str,Any]=field(default_factory=dict)
    passive_findings: tuple[Mapping[str,Any],...]=field(default_factory=tuple)
    github_actions: tuple[str,...]=()
    local_authority: bool=True
    github_review_surface_only: bool=True
    scan_once: bool=True
    remote_mutation_allowed: bool=False
    creates_issue: bool=False
    updates_project: bool=False
    pushes_commit: bool=False
    opens_pull_request: bool=False
    executes_runtime: bool=False
    starts_postgresql: bool=False
    starts_openvino: bool=False
    starts_qdrant: bool=False
    modifies_scheduler_run: bool=False
    creates_runtime_manager: bool=False
    def to_mapping(self)->dict[str,Any]:
        return {'schema':HANDOFF_SCHEMA,'github_scan_once_handoff':True,'valid':self.valid,'issues':list(self.issues),'request':self.request.to_mapping(),'handoff_ref':self.handoff_ref,'sql_ref':self.sql_ref,'embedding_ref':self.embedding_ref,'source_reports':dict(self.source_reports),'summary':dict(self.summary),'passive_findings':[dict(x) for x in self.passive_findings],'github_actions':list(self.github_actions),'local_authority':self.local_authority,'github_review_surface_only':self.github_review_surface_only,'scan_once':self.scan_once,'remote_mutation_allowed':self.remote_mutation_allowed,'creates_issue':self.creates_issue,'updates_project':self.updates_project,'pushes_commit':self.pushes_commit,'opens_pull_request':self.opens_pull_request,'executes_runtime':self.executes_runtime,'starts_postgresql':self.starts_postgresql,'starts_openvino':self.starts_openvino,'starts_qdrant':self.starts_qdrant,'modifies_scheduler_run':self.modifies_scheduler_run,'creates_runtime_manager':self.creates_runtime_manager}

def validate_closed_frame_for_github_handoff(frame: Mapping[str,Any])->tuple[str,...]:
    issues=[]
    if frame.get('valid') is not True: issues.append('closed ResultFrame must be valid')
    if not str(frame.get('sql_ref') or '').startswith('sql:'): issues.append('closed ResultFrame must expose a typed sql_ref')
    if not str(frame.get('embedding_ref') or '').startswith('embedding:'): issues.append('closed ResultFrame must expose a typed embedding_ref')
    if frame.get('sql_remains_authority') is not True: issues.append('closed ResultFrame must keep SQL as authority')
    if frame.get('qdrant_projection_recall_refs_only') is not True: issues.append('closed ResultFrame must keep Qdrant ref-only')
    if frame.get('executes_runtime') is not False: issues.append('GitHub handoff input must be non-runtime')
    if frame.get('starts_postgresql') is not False: issues.append('GitHub handoff input must not start PostgreSQL')
    if frame.get('starts_openvino') is not False: issues.append('GitHub handoff input must not start OpenVINO')
    if frame.get('starts_qdrant') is not False: issues.append('GitHub handoff input must not start Qdrant')
    return tuple(issues)

def validate_passive_report_for_github_handoff(report: Mapping[str,Any])->tuple[str,...]:
    issues=[]
    if report.get('valid') is not True: issues.append('PassiveSupervisor report must be valid')
    if report.get('passive_supervisor_observation_only') is not True: issues.append('PassiveSupervisor report must be observation-only')
    if report.get('accepted_fact_count',0) <= 0: issues.append('PassiveSupervisor report must accept at least one fact')
    if report.get('rejected_fact_count',0) != 0: issues.append('PassiveSupervisor report must have zero rejected facts')
    if report.get('command_like_fact_count',0) != 0: issues.append('PassiveSupervisor report must have zero command-like facts')
    if report.get('runtime_violation_count',0) != 0: issues.append('PassiveSupervisor report must have zero runtime violations')
    if report.get('publishes_events') is not False: issues.append('PassiveSupervisor report must not publish events')
    return tuple(issues)

def validate_github_scan_once_request(request: GitHubScanOnceHandoffRequest)->tuple[str,...]:
    issues=[]
    if not request.repository or '/' not in request.repository: issues.append('repository must be owner/name')
    if not request.operator_intent: issues.append('operator_intent must not be empty')
    if not request.target_surface.startswith('github_'): issues.append('target_surface must be a GitHub review surface')
    if request.allow_remote_mutation: issues.append('remote mutation is forbidden in 0267')
    return tuple(issues)

def _stable_handoff_ref(request:GitHubScanOnceHandoffRequest, frame:Mapping[str,Any], passive:Mapping[str,Any])->str:
    d=hashlib.sha256();
    for part in (request.repository, str(frame.get('sql_ref') or ''), str(frame.get('embedding_ref') or ''), str(passive.get('accepted_fact_count') or 0)):
        d.update(part.encode()); d.update(b'\0')
    return 'github-scan-once-handoff:'+d.hexdigest()[:16]

def _passive_findings(report:Mapping[str,Any])->tuple[Mapping[str,Any],...]:
    findings=report.get('findings',[])
    return tuple(x for x in findings if isinstance(x, Mapping)) if isinstance(findings, list) else ()

def build_github_scan_once_handoff(*, closed_frame:Mapping[str,Any], passive_report:Mapping[str,Any], request:GitHubScanOnceHandoffRequest, source_reports:Mapping[str,str])->GitHubScanOnceHandoff:
    issues=[]; issues.extend(validate_github_scan_once_request(request)); issues.extend(validate_closed_frame_for_github_handoff(closed_frame)); issues.extend(validate_passive_report_for_github_handoff(passive_report))
    sql_ref=str(closed_frame.get('sql_ref') or ''); emb=str(closed_frame.get('embedding_ref') or '')
    summary={'sql_ref':sql_ref,'embedding_ref':emb,'projection_point_count':closed_frame.get('projection_point_count',0),'recall_hit_count':closed_frame.get('recall_hit_count',0),'hydrated_count':closed_frame.get('hydrated_count',0),'missing_count':closed_frame.get('missing_count',0),'accepted_fact_count':passive_report.get('accepted_fact_count',0),'target_surface':request.target_surface}
    return GitHubScanOnceHandoff(valid=not issues,issues=tuple(issues),request=request,handoff_ref='' if issues else _stable_handoff_ref(request,closed_frame,passive_report),sql_ref=sql_ref,embedding_ref=emb,source_reports=source_reports,summary=summary,passive_findings=_passive_findings(passive_report),github_actions=('review_closed_result_frame','optionally_create_operator_ticket_after_manual_validation','never_mutate_remote_without_future_gate'))

def load_json(path:Path)->dict[str,Any]: return json.loads(path.read_text(encoding='utf-8'))
def write_handoff(output:Path,handoff:GitHubScanOnceHandoff)->None:
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(handoff.to_mapping(),indent=2,sort_keys=True)+'\n',encoding='utf-8')
