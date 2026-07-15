"""Strict request/advisory separation for GitHub-produced artifacts."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any
import hashlib, json, re

REQUEST_SCHEMA="missipy.github.authoritative_request.v1"
ADVISORY_SCHEMA="missipy.github.copilot_advisory.v1"
ADVISORY_SCHEMA_V1=ADVISORY_SCHEMA
ADVISORY_SCHEMA_V2="missipy.github.copilot_advisory.v2"
MANIFEST_SCHEMA="missipy.github.dual_artifact_manifest.v1"
_DIGEST=re.compile(r"^[0-9a-f]{64}$")
_REPO=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

class GitHubDualArtifactContractError(ValueError): pass

def _text(name,v):
 if not isinstance(v,str) or not v.strip(): raise GitHubDualArtifactContractError(f"{name} must be non-empty")
 return v.strip()
def _digest(name,v):
 if not isinstance(v,str) or not _DIGEST.fullmatch(v): raise GitHubDualArtifactContractError(f"{name} must be sha256")
 return v
def _strings(name,v,empty=True):
 vals=tuple(str(x).strip() for x in v if str(x).strip())
 if not empty and not vals: raise GitHubDualArtifactContractError(f"{name} must not be empty")
 return tuple(dict.fromkeys(vals))
def canonical_json_bytes(payload: Mapping[str,Any])->bytes:
 return (json.dumps(dict(payload),ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()
def sha256_bytes(data:bytes)->str: return hashlib.sha256(data).hexdigest()

@dataclass(frozen=True,slots=True)
class GitHubAuthoritativeRequestArtifact:
 origin_frame_id:str; ticket_revision_id:str; artifact_ref:str; repository:str
 issue_number:int; title:str; body:str; issue_url:str; labels:tuple[str,...]=()
 actor:str=""; event_name:str="issues"; metadata:tuple[tuple[str,str],...]=()
 schema:str=REQUEST_SCHEMA; authoritative:bool=True; advisory_content_embedded:bool=False
 remote_mutation_requested:bool=False
 def __post_init__(self):
  for n in ("origin_frame_id","ticket_revision_id","artifact_ref","title","body","issue_url"): object.__setattr__(self,n,_text(n,getattr(self,n)))
  if not self.artifact_ref.startswith("github-request:"): raise GitHubDualArtifactContractError("artifact_ref must start with github-request:")
  if not _REPO.fullmatch(self.repository): raise GitHubDualArtifactContractError("repository must be owner/name")
  if isinstance(self.issue_number,bool) or self.issue_number<=0: raise GitHubDualArtifactContractError("issue_number must be > 0")
  object.__setattr__(self,"labels",_strings("labels",self.labels))
  object.__setattr__(self,"metadata",tuple(dict(self.metadata).items()))
  if self.schema!=REQUEST_SCHEMA or not self.authoritative or self.advisory_content_embedded or self.remote_mutation_requested: raise GitHubDualArtifactContractError("request authority flags are locked")
 def to_mapping(self): return {"schema":self.schema,"origin_frame_id":self.origin_frame_id,"ticket_revision_id":self.ticket_revision_id,"artifact_ref":self.artifact_ref,"repository":self.repository,"issue_number":self.issue_number,"title":self.title,"body":self.body,"issue_url":self.issue_url,"labels":list(self.labels),"actor":self.actor,"event_name":self.event_name,"metadata":dict(self.metadata),"authoritative":True,"advisory_content_embedded":False,"remote_mutation_requested":False}
 @classmethod
 def from_mapping(cls,m): return cls(origin_frame_id=m["origin_frame_id"],ticket_revision_id=m["ticket_revision_id"],artifact_ref=m["artifact_ref"],repository=m["repository"],issue_number=m["issue_number"],title=m["title"],body=m["body"],issue_url=m["issue_url"],labels=tuple(m.get("labels",())),actor=str(m.get("actor","")),event_name=str(m.get("event_name","issues")),metadata=tuple(dict(m.get("metadata",{})).items()),schema=str(m.get("schema",REQUEST_SCHEMA)),authoritative=bool(m.get("authoritative",False)),advisory_content_embedded=bool(m.get("advisory_content_embedded",False)),remote_mutation_requested=bool(m.get("remote_mutation_requested",False)))

@dataclass(frozen=True,slots=True)
class GitHubCopilotAdvisoryArtifact:
 origin_frame_id:str; ticket_revision_id:str; artifact_ref:str; request_artifact_ref:str
 prompt_digest:str; response_digest:str; summary:str; suggested_route:str
 assumptions:tuple[str,...]=(); questions:tuple[str,...]=(); risks:tuple[str,...]=(); confidence:float=0.0
 producer_kind:str="github_copilot_cli"; schema:str=ADVISORY_SCHEMA
 trusted:bool=False; usable_as_hint:bool=True; usable_as_authority:bool=False
 def __post_init__(self):
  for n in ("origin_frame_id","ticket_revision_id","artifact_ref","request_artifact_ref","summary","suggested_route"): object.__setattr__(self,n,_text(n,getattr(self,n)))
  if not self.artifact_ref.startswith("github-advisory:") or not self.request_artifact_ref.startswith("github-request:"): raise GitHubDualArtifactContractError("advisory refs are invalid")
  _digest("prompt_digest",self.prompt_digest); _digest("response_digest",self.response_digest)
  for n in ("assumptions","questions","risks"): object.__setattr__(self,n,_strings(n,getattr(self,n)))
  if not 0<=self.confidence<=1: raise GitHubDualArtifactContractError("confidence must be between 0 and 1")
  if self.schema!=ADVISORY_SCHEMA or self.trusted or not self.usable_as_hint or self.usable_as_authority: raise GitHubDualArtifactContractError("advisory authority flags are locked")
 def to_mapping(self): return {"schema":self.schema,"origin_frame_id":self.origin_frame_id,"ticket_revision_id":self.ticket_revision_id,"artifact_ref":self.artifact_ref,"request_artifact_ref":self.request_artifact_ref,"prompt_digest":self.prompt_digest,"response_digest":self.response_digest,"summary":self.summary,"suggested_route":self.suggested_route,"assumptions":list(self.assumptions),"questions":list(self.questions),"risks":list(self.risks),"confidence":self.confidence,"producer_kind":self.producer_kind,"trusted":False,"usable_as_hint":True,"usable_as_authority":False}
 @classmethod
 def from_mapping(cls,m): return cls(origin_frame_id=m["origin_frame_id"],ticket_revision_id=m["ticket_revision_id"],artifact_ref=m["artifact_ref"],request_artifact_ref=m["request_artifact_ref"],prompt_digest=m["prompt_digest"],response_digest=m["response_digest"],summary=m["summary"],suggested_route=m["suggested_route"],assumptions=tuple(m.get("assumptions",())),questions=tuple(m.get("questions",())),risks=tuple(m.get("risks",())),confidence=float(m.get("confidence",0)),producer_kind=str(m.get("producer_kind","github_copilot_cli")),schema=str(m.get("schema",ADVISORY_SCHEMA)),trusted=bool(m.get("trusted",False)),usable_as_hint=bool(m.get("usable_as_hint",False)),usable_as_authority=bool(m.get("usable_as_authority",False)))


_COPILOT_ADVISORY_V2_KEYS = frozenset({
    "schema",
    "origin_frame_id",
    "ticket_revision_id",
    "artifact_ref",
    "request_artifact_ref",
    "prompt_digest",
    "response_digest",
    "concrete_objective",
    "expected_result",
    "provided_constraints",
    "success_criteria",
    "producer_kind",
    "trusted",
    "usable_as_hint",
    "usable_as_authority",
})


def _strict_strings(name, value, *, empty=True):
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise GitHubDualArtifactContractError(f"{name} must be an array")
    values = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise GitHubDualArtifactContractError(
                f"{name} entries must be non-empty strings"
            )
        values.append(item.strip())
    normalized = tuple(dict.fromkeys(values))
    if not empty and not normalized:
        raise GitHubDualArtifactContractError(f"{name} must not be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class GitHubCopilotFirstOpinionAdvisoryArtifact:
    origin_frame_id: str
    ticket_revision_id: str
    artifact_ref: str
    request_artifact_ref: str
    prompt_digest: str
    response_digest: str
    concrete_objective: str
    expected_result: str
    provided_constraints: tuple[str, ...] = ()
    success_criteria: tuple[str, ...] = ()
    producer_kind: str = "github_copilot_cli"
    schema: str = ADVISORY_SCHEMA_V2
    trusted: bool = False
    usable_as_hint: bool = True
    usable_as_authority: bool = False

    def __post_init__(self):
        for name in (
            "origin_frame_id",
            "ticket_revision_id",
            "artifact_ref",
            "request_artifact_ref",
            "concrete_objective",
            "expected_result",
            "producer_kind",
        ):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        if not self.artifact_ref.startswith("github-advisory:"):
            raise GitHubDualArtifactContractError("advisory artifact_ref is invalid")
        if not self.request_artifact_ref.startswith("github-request:"):
            raise GitHubDualArtifactContractError(
                "advisory request_artifact_ref is invalid"
            )
        _digest("prompt_digest", self.prompt_digest)
        _digest("response_digest", self.response_digest)
        object.__setattr__(
            self,
            "provided_constraints",
            _strict_strings("provided_constraints", self.provided_constraints),
        )
        object.__setattr__(
            self,
            "success_criteria",
            _strict_strings(
                "success_criteria",
                self.success_criteria,
                empty=False,
            ),
        )
        if (
            self.schema != ADVISORY_SCHEMA_V2
            or self.trusted is not False
            or self.usable_as_hint is not True
            or self.usable_as_authority is not False
        ):
            raise GitHubDualArtifactContractError(
                "advisory v2 authority flags are locked"
            )

    def to_mapping(self):
        return {
            "schema": self.schema,
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "artifact_ref": self.artifact_ref,
            "request_artifact_ref": self.request_artifact_ref,
            "prompt_digest": self.prompt_digest,
            "response_digest": self.response_digest,
            "concrete_objective": self.concrete_objective,
            "expected_result": self.expected_result,
            "provided_constraints": list(self.provided_constraints),
            "success_criteria": list(self.success_criteria),
            "producer_kind": self.producer_kind,
            "trusted": False,
            "usable_as_hint": True,
            "usable_as_authority": False,
        }

    @classmethod
    def from_mapping(cls, mapping):
        actual = frozenset(mapping)
        if actual != _COPILOT_ADVISORY_V2_KEYS:
            missing = sorted(_COPILOT_ADVISORY_V2_KEYS - actual)
            extra = sorted(actual - _COPILOT_ADVISORY_V2_KEYS)
            raise GitHubDualArtifactContractError(
                f"advisory v2 field mismatch: missing={missing}, extra={extra}"
            )
        return cls(
            origin_frame_id=mapping["origin_frame_id"],
            ticket_revision_id=mapping["ticket_revision_id"],
            artifact_ref=mapping["artifact_ref"],
            request_artifact_ref=mapping["request_artifact_ref"],
            prompt_digest=mapping["prompt_digest"],
            response_digest=mapping["response_digest"],
            concrete_objective=mapping["concrete_objective"],
            expected_result=mapping["expected_result"],
            provided_constraints=mapping["provided_constraints"],
            success_criteria=mapping["success_criteria"],
            producer_kind=mapping["producer_kind"],
            schema=mapping["schema"],
            trusted=mapping["trusted"],
            usable_as_hint=mapping["usable_as_hint"],
            usable_as_authority=mapping["usable_as_authority"],
        )


def parse_copilot_advisory_artifact(mapping):
    schema = str(mapping.get("schema", ADVISORY_SCHEMA_V1))
    if schema == ADVISORY_SCHEMA_V1:
        return GitHubCopilotAdvisoryArtifact.from_mapping(mapping)
    if schema == ADVISORY_SCHEMA_V2:
        return GitHubCopilotFirstOpinionAdvisoryArtifact.from_mapping(mapping)
    raise GitHubDualArtifactContractError(
        f"unsupported Copilot advisory schema: {schema}"
    )

@dataclass(frozen=True,slots=True)
class GitHubDualArtifactManifest:
 manifest_ref:str; origin_frame_id:str; ticket_revision_id:str
 request_artifact_ref:str; request_filename:str; request_sha256:str
 advisory_artifact_ref:str|None=None; advisory_filename:str|None=None; advisory_sha256:str|None=None
 schema:str=MANIFEST_SCHEMA; request_is_authority:bool=True; advisory_is_authority:bool=False
 def __post_init__(self):
  for n in ("manifest_ref","origin_frame_id","ticket_revision_id","request_artifact_ref","request_filename"): object.__setattr__(self,n,_text(n,getattr(self,n)))
  _digest("request_sha256",self.request_sha256)
  if not self.manifest_ref.startswith("github-dual-manifest:") or not self.request_artifact_ref.startswith("github-request:"): raise GitHubDualArtifactContractError("manifest refs are invalid")
  advisory_fields=(self.advisory_artifact_ref,self.advisory_filename,self.advisory_sha256)
  if any(x is not None for x in advisory_fields) and not all(x is not None for x in advisory_fields): raise GitHubDualArtifactContractError("advisory manifest fields are all-or-none")
  if self.advisory_sha256 is not None: _digest("advisory_sha256",self.advisory_sha256)
  if self.advisory_artifact_ref==self.request_artifact_ref or self.advisory_filename==self.request_filename: raise GitHubDualArtifactContractError("request and advisory must be physically distinct")
  if self.schema!=MANIFEST_SCHEMA or not self.request_is_authority or self.advisory_is_authority: raise GitHubDualArtifactContractError("manifest authority flags are locked")
 def to_mapping(self): return {"schema":self.schema,"manifest_ref":self.manifest_ref,"origin_frame_id":self.origin_frame_id,"ticket_revision_id":self.ticket_revision_id,"request_artifact_ref":self.request_artifact_ref,"request_filename":self.request_filename,"request_sha256":self.request_sha256,"advisory_artifact_ref":self.advisory_artifact_ref,"advisory_filename":self.advisory_filename,"advisory_sha256":self.advisory_sha256,"request_is_authority":True,"advisory_is_authority":False}
 @classmethod
 def from_mapping(cls,m): return cls(manifest_ref=m["manifest_ref"],origin_frame_id=m["origin_frame_id"],ticket_revision_id=m["ticket_revision_id"],request_artifact_ref=m["request_artifact_ref"],request_filename=m["request_filename"],request_sha256=m["request_sha256"],advisory_artifact_ref=m.get("advisory_artifact_ref"),advisory_filename=m.get("advisory_filename"),advisory_sha256=m.get("advisory_sha256"),schema=str(m.get("schema",MANIFEST_SCHEMA)),request_is_authority=bool(m.get("request_is_authority",False)),advisory_is_authority=bool(m.get("advisory_is_authority",False)))

def build_dual_artifact_manifest(request,request_bytes,advisory=None,advisory_bytes=None,request_filename="authoritative_request.json",advisory_filename="copilot_advisory.json"):
 if advisory is None and advisory_bytes is not None or advisory is not None and advisory_bytes is None: raise GitHubDualArtifactContractError("advisory and advisory_bytes must be supplied together")
 if advisory and (advisory.origin_frame_id!=request.origin_frame_id or advisory.ticket_revision_id!=request.ticket_revision_id or advisory.request_artifact_ref!=request.artifact_ref): raise GitHubDualArtifactContractError("advisory correlation mismatch")
 identity=request.artifact_ref+"\0"+sha256_bytes(request_bytes)+"\0"+("" if advisory_bytes is None else sha256_bytes(advisory_bytes))
 return GitHubDualArtifactManifest(manifest_ref="github-dual-manifest:"+hashlib.sha256(identity.encode()).hexdigest()[:16],origin_frame_id=request.origin_frame_id,ticket_revision_id=request.ticket_revision_id,request_artifact_ref=request.artifact_ref,request_filename=request_filename,request_sha256=sha256_bytes(request_bytes),advisory_artifact_ref=None if advisory is None else advisory.artifact_ref,advisory_filename=None if advisory is None else advisory_filename,advisory_sha256=None if advisory_bytes is None else sha256_bytes(advisory_bytes))

def validate_dual_artifact_correlation(request,manifest,advisory=None):
 issues=[]
 if manifest.request_artifact_ref!=request.artifact_ref or manifest.origin_frame_id!=request.origin_frame_id or manifest.ticket_revision_id!=request.ticket_revision_id: issues.append("request/manifest correlation mismatch")
 if advisory is not None and (manifest.advisory_artifact_ref!=advisory.artifact_ref or advisory.request_artifact_ref!=request.artifact_ref or advisory.origin_frame_id!=request.origin_frame_id or advisory.ticket_revision_id!=request.ticket_revision_id): issues.append("advisory correlation mismatch")
 return tuple(issues)
