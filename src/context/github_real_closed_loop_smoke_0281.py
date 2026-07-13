"""Real local smoke for the GitHub dual-artifact closed loop.

The composition starts from immutable members resolved from the configured
server dataset and a ready 0281-r3 run-group report. It validates correlation
through 0281-r2/0275, executes the existing Scheduler/fake-laboratory path
through 0281-r5, and produces the exact publication preview consumed by
0281-r6.

This module never reads a Git checkout or a manual Actions download tree.
It does not fetch from GitHub, create a Scheduler, write files, or perform
remote mutation. The caller injects the existing Scheduler and all
durable/vector/observation adapters.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import json
from typing import Any

from context.fake_laboratory_closed_local_handoff_0274 import (
    FakeLaboratoryClosedHandoffCommand,
)
from context.fake_laboratory_deliberation_composition_0274 import (
    FakeLaboratoryDeliberationCommand,
)
from context.fake_laboratory_existing_scheduler_closed_loop_smoke_0274 import (
    FakeLaboratoryClosedLoopSmokeCommand,
)
from context.fake_laboratory_recall_closed_result_frame_0274 import (
    LaboratoryRecallClosureCommand,
)
from context.github_controlled_advisory_issue_publication_0281 import (
    GitHubControlledAdvisoryIssuePublicationCommand,
    plan_github_controlled_advisory_issue_publication,
)
from context.github_dual_artifact_laboratory_smoke_0275 import (
    GitHubDualArtifactLaboratorySmokeCommand,
)
from context.github_dual_artifact_run_assembly_0281 import (
    GitHubDualArtifactRunAssemblyCommand,
    GitHubDualArtifactRunAssemblyPolicy,
    GitHubDualArtifactRunMember,
    run_github_dual_artifact_run_assembly,
)
from context.github_operator_laboratory_advisory_projection_0281 import (
    GitHubOperatorLaboratoryAdvisoryProjectionCommand,
    run_github_operator_laboratory_advisory_projection,
)
from context.laboratory_framework_contract_0273 import (
    LaboratoryResourceBudget,
)
from context.server_oriented_deliberation_cycle import ServerOrientation
from context.source_candidate import SourceCandidateDecision

SCHEMA = "missipy.github.real_closed_loop_smoke.v1"
DEFAULT_SPECIALIST_REFS = (
    "specialist:technical",
    "specialist:validator",
)
DEFAULT_DOCUMENT_KINDS = ("analysis", "validation")
_EXPECTED_ARTIFACT_BY_FILENAME = {
    "authoritative_request.json": "autodoc-authoritative-request",
    "copilot_advisory.json": "autodoc-copilot-advisory",
    "dual_artifact_manifest.json": "autodoc-dual-artifact-manifest",
}


@dataclass(frozen=True, slots=True)
class GitHubRealClosedLoopSmokeCommand:
    repository: str
    run_id: str
    issue_number: int
    members: tuple[GitHubDualArtifactRunMember, ...]
    run_group_report_ref: str
    policy_decision_id: str
    operator_reason: str
    require_advisory: bool = True
    requested_specialist_refs: tuple[str, ...] = DEFAULT_SPECIALIST_REFS
    requested_document_kinds: tuple[str, ...] = DEFAULT_DOCUMENT_KINDS
    publish_observations: bool = True
    verify_sql_replay: bool = True
    timeout_per_visit: float = 1.0

    def __post_init__(self) -> None:
        if "/" not in self.repository:
            raise ValueError("repository must be owner/name")
        if not self.run_id.strip():
            raise ValueError("run_id must not be empty")
        if self.issue_number <= 0:
            raise ValueError("issue_number must be > 0")
        if not isinstance(self.members, tuple):
            object.__setattr__(self, "members", tuple(self.members))
        if not self.run_group_report_ref.startswith(
            "dataset-index:github-dual-artifact-run-group:"
        ):
            raise ValueError(
                "run_group_report_ref must identify the imported run-group"
            )
        if not self.policy_decision_id.startswith("policy:"):
            raise ValueError("policy_decision_id must start with policy:")
        if not self.operator_reason.strip():
            raise ValueError("operator_reason must not be empty")
        if not self.requested_specialist_refs:
            raise ValueError("at least one specialist is required")
        if not self.requested_document_kinds:
            raise ValueError("at least one document kind is required")
        if self.timeout_per_visit <= 0:
            raise ValueError("timeout_per_visit must be > 0")


@dataclass(frozen=True, slots=True)
class GitHubRealClosedLoopSmokeResult:
    valid: bool
    issues: tuple[str, ...]
    repository: str
    run_id: str
    issue_number: int
    run_group_report_ref: str
    assembly: Mapping[str, Any] = field(default_factory=dict)
    laboratory_projection: Mapping[str, Any] = field(default_factory=dict)
    publication_preview: Mapping[str, Any] = field(default_factory=dict)
    publication_plan: Mapping[str, Any] = field(default_factory=dict)
    phase_trace: tuple[str, ...] = (
        "0281-r2-run-assembly",
        "0275-dual-artifact-intake",
        "0281-r5-operator-laboratory-advisory-projection",
        "0274-existing-scheduler-fake-laboratory-closed-loop",
        "0281-r6-controlled-publication-plan",
    )
    output_files_written: bool = False
    existing_scheduler_used: bool = True
    scheduler_created: bool = False
    scheduler_modified: bool = False
    parallel_orchestrator_created: bool = False
    github_mutation_performed: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "repository": self.repository,
            "run_id": self.run_id,
            "issue_number": self.issue_number,
            "run_group_report_ref": self.run_group_report_ref,
            "input_source": "configured_server_dataset",
            "assembly": dict(self.assembly),
            "laboratory_projection": dict(self.laboratory_projection),
            "publication_preview": dict(self.publication_preview),
            "publication_plan": dict(self.publication_plan),
            "phase_trace": list(self.phase_trace),
            "output_files_written": False,
            "existing_scheduler_used": True,
            "scheduler_created": False,
            "scheduler_modified": False,
            "parallel_orchestrator_created": False,
            "github_mutation_performed": False,
            "publication_execution_required": True,
        }


async def run_github_real_closed_loop_smoke(
    scheduler: Any,
    command: GitHubRealClosedLoopSmokeCommand,
    **laboratory_dependencies: Any,
) -> GitHubRealClosedLoopSmokeResult:
    """Execute the real local chain without GitHub mutation."""

    assembly = run_github_dual_artifact_run_assembly(
        GitHubDualArtifactRunAssemblyCommand(
            repository=command.repository,
            run_id=command.run_id,
            members=command.members,
        ),
        GitHubDualArtifactRunAssemblyPolicy(
            allow_missing_advisory=not command.require_advisory,
        ),
    )
    assembly_mapping = assembly.to_mapping()
    if not assembly.valid:
        return _result(
            command,
            issues=assembly.issues,
            assembly=assembly_mapping,
        )

    intake = _mapping(assembly_mapping.get("intake"))
    request = _mapping(intake.get("request"))
    candidate = _mapping(intake.get("source_candidate"))
    issues = list(_validate_request_identity(command, request))
    if issues:
        return _result(
            command,
            issues=issues,
            assembly=assembly_mapping,
        )

    selected = _select_required_member_bytes(command.members)
    if selected["request"] is None or selected["manifest"] is None:
        return _result(
            command,
            issues=("run assembly did not retain required artifact bytes",),
            assembly=assembly_mapping,
        )

    laboratory_command = build_real_closed_loop_laboratory_command(
        command,
        request=request,
        source_candidate=candidate,
    )
    smoke_command = GitHubDualArtifactLaboratorySmokeCommand(
        decision=SourceCandidateDecision(
            action="promote",
            reason=command.operator_reason,
        ),
        laboratory=laboratory_command,
        policy_decision_id=command.policy_decision_id,
    )
    projection_result = (
        await run_github_operator_laboratory_advisory_projection(
            scheduler,
            selected["request"],
            selected["manifest"],
            selected["advisory"],
            GitHubOperatorLaboratoryAdvisoryProjectionCommand(
                smoke=smoke_command,
                require_advisory=command.require_advisory,
            ),
            **laboratory_dependencies,
        )
    )
    projection_mapping = projection_result.to_mapping()
    if not projection_result.valid:
        return _result(
            command,
            issues=projection_result.issues,
            assembly=assembly_mapping,
            laboratory_projection=projection_mapping,
        )

    preview = _mapping(projection_mapping.get("publication_preview"))
    plan = plan_github_controlled_advisory_issue_publication(
        GitHubControlledAdvisoryIssuePublicationCommand(
            repository=command.repository,
            issue_number=command.issue_number,
            policy_decision_id=command.policy_decision_id,
            operator_decision="approve",
            publication_preview=preview,
            existing_comments=(),
        )
    )
    plan_mapping = plan.to_mapping()
    issues = []
    if not plan.valid:
        issues.extend(getattr(plan, "issues", ()))
    if plan.action != "create":
        issues.append(
            "fresh local smoke publication plan must have action=create"
        )
    if projection_mapping.get("github_mutation_performed") is True:
        issues.append("laboratory projection mutated GitHub")
    if projection_mapping.get("scheduler_created") is True:
        issues.append("laboratory projection created a Scheduler")
    return _result(
        command,
        issues=issues,
        assembly=assembly_mapping,
        laboratory_projection=projection_mapping,
        publication_preview=preview,
        publication_plan=plan_mapping,
    )


def build_real_closed_loop_laboratory_command(
    command: GitHubRealClosedLoopSmokeCommand,
    *,
    request: Mapping[str, Any],
    source_candidate: Mapping[str, Any],
) -> FakeLaboratoryClosedLoopSmokeCommand:
    """Build the existing 0274 command from authoritative request identity."""

    candidate_id = _required_text(
        "source_candidate.candidate_id",
        source_candidate.get("candidate_id"),
    )
    title = _required_text("request.title", request.get("title"))
    body = _required_text("request.body", request.get("body"))
    request_artifact_ref = _required_text(
        "request.artifact_ref",
        request.get("artifact_ref"),
    )
    short = _digest(
        "\0".join(
            (
                command.repository,
                command.run_id,
                str(command.issue_number),
                request_artifact_ref,
                candidate_id,
            )
        )
    )
    local_artifact_ref = f"artifact:github-request:{short}"
    orientation = ServerOrientation(
        orientation_ref=f"orientation:github-run:{short}",
        artifact_ref=local_artifact_ref,
        source_ref=local_artifact_ref,
        sql_context_ref=f"sql:github-run:{short}",
        title=title,
        intent=(
            "Traiter localement la requête GitHub autoritative, utiliser "
            "l’avis Copilot seulement comme hypothèse, puis produire une "
            "prévisualisation de publication contrôlée."
        ),
        requested_specialist_refs=command.requested_specialist_refs,
        requested_document_kinds=command.requested_document_kinds,
        do_directives=(
            "Conserver les preuves et les références de corrélation.",
            "Fonder la synthèse sur la requête autoritative.",
        ),
        avoid_directives=(
            "Ne pas publier sans la gate opérateur 0281-r6.",
            "Ne pas transformer l’avis Copilot en autorité.",
        ),
        context_refs=(f"ctx:github-run:{short}",),
        metadata=(
            ("github_repository", command.repository),
            ("github_run_id", command.run_id),
            ("github_issue_number", str(command.issue_number)),
            ("request_artifact_ref", request_artifact_ref),
            ("request_body_sha256", hashlib.sha256(body.encode("utf-8")).hexdigest()),
        ),
    )
    deliberation = FakeLaboratoryDeliberationCommand(
        orientation=orientation,
        artifact_ref=local_artifact_ref,
        source_candidate_ref=f"source-candidate:{candidate_id}",
        target_ref=(
            f"github:issue:{command.repository}/{command.issue_number}"
        ),
        context_generation=0,
        resource_budget=LaboratoryResourceBudget(
            max_duration_ms=2_000,
            max_context_refs=32,
            max_evidence_refs=32,
            max_followup_requests=8,
            max_specialist_messages=16,
            max_external_calls=0,
            allow_network=False,
        ),
    )
    return FakeLaboratoryClosedLoopSmokeCommand(
        deliberation=deliberation,
        handoff=FakeLaboratoryClosedHandoffCommand(
            execute=True,
            policy_decision_id=(
                command.policy_decision_id + ":laboratory-handoff"
            ),
            vector_execute=True,
            publish_observations=command.publish_observations,
        ),
        recall=LaboratoryRecallClosureCommand(
            execute=True,
            policy_decision_id=(
                command.policy_decision_id + ":laboratory-recall"
            ),
            publish_observations=command.publish_observations,
        ),
        verify_sql_replay=command.verify_sql_replay,
        timeout_per_visit=command.timeout_per_visit,
    )


@dataclass(frozen=True, slots=True)
class ImportedGitHubRunBundle:
    """Ready run-group report plus verified immutable raw dataset members."""

    repository: str
    run_id: str
    report_path: Path
    report_ref: str
    raw_run_root: Path
    members: tuple[GitHubDualArtifactRunMember, ...]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "run_id": self.run_id,
            "report_path": str(self.report_path),
            "report_ref": self.report_ref,
            "raw_run_root": str(self.raw_run_root),
            "member_count": len(self.members),
            "members": [member.to_mapping() for member in self.members],
        }


def load_imported_github_run_bundle(
    *,
    dataset_raw_path: Path,
    dataset_index_path: Path,
    repository: str,
    run_id: str,
) -> ImportedGitHubRunBundle:
    """Resolve one ready r3 run exclusively through the server dataset."""

    repository_slug = repository.replace("/", "__")
    report_path = (
        dataset_index_path
        / "github_dual_artifact_run_groups"
        / repository_slug
        / f"{run_id}.json"
    )
    report = _read_json_mapping(report_path, name="run-group report")
    if report.get("schema") != (
        "missipy.github.dual_artifact_fetch_run_group.v1"
    ):
        raise ValueError("unexpected run-group report schema")
    if report.get("status") != "ready":
        raise ValueError("run-group report must have status=ready")
    if report.get("repository") != repository:
        raise ValueError("run-group repository does not match config")
    if str(report.get("run_id", "")) != run_id:
        raise ValueError("run-group run_id does not match command")

    collected = report.get("collected_files")
    if not isinstance(collected, list):
        raise ValueError("run-group collected_files must be a JSON array")

    raw_run_root = (
        dataset_raw_path / repository_slug / run_id
    ).resolve()
    if not raw_run_root.exists() or not raw_run_root.is_dir():
        raise ValueError(
            f"imported raw run directory is missing: {raw_run_root}"
        )
    if raw_run_root.is_symlink():
        raise ValueError("imported raw run directory must not be a symlink")

    members: list[GitHubDualArtifactRunMember] = []
    seen_filenames: set[str] = set()
    for item in collected:
        if not isinstance(item, Mapping):
            raise ValueError("collected file entry must be a JSON object")
        artifact_name = str(item.get("artifact_name", "")).strip()
        filename = str(item.get("filename", "")).strip()
        relative_value = str(item.get("relative_path", "")).strip()
        expected_artifact = _EXPECTED_ARTIFACT_BY_FILENAME.get(filename)
        if expected_artifact is None:
            continue
        if artifact_name != expected_artifact:
            raise ValueError(
                f"artifact identity mismatch for {filename}"
            )
        if filename in seen_filenames:
            raise ValueError(f"duplicate imported member: {filename}")

        relative = Path(relative_value)
        if (
            not relative_value
            or relative.is_absolute()
            or ".." in relative.parts
        ):
            raise ValueError(
                f"unsafe imported relative_path: {relative_value}"
            )
        path = (raw_run_root / relative).resolve()
        if not path.is_relative_to(raw_run_root):
            raise ValueError(
                f"imported member escaped raw dataset: {relative_value}"
            )
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"imported member is missing: {path}")

        content = path.read_bytes()
        expected_size = int(item.get("size_bytes", -1))
        expected_sha = str(item.get("sha256", "")).strip()
        if expected_size != len(content):
            raise ValueError(f"size mismatch for imported {filename}")
        if hashlib.sha256(content).hexdigest() != expected_sha:
            raise ValueError(f"sha256 mismatch for imported {filename}")

        members.append(
            GitHubDualArtifactRunMember(
                artifact_name=artifact_name,
                filename=filename,
                content=content,
            )
        )
        seen_filenames.add(filename)

    required = {
        "authoritative_request.json",
        "dual_artifact_manifest.json",
    }
    missing = sorted(required - seen_filenames)
    if missing:
        raise ValueError(
            "ready run-group is missing imported member(s): "
            + ", ".join(missing)
        )

    report_ref = (
        "dataset-index:github-dual-artifact-run-group:"
        f"{repository_slug}:{run_id}"
    )
    return ImportedGitHubRunBundle(
        repository=repository,
        run_id=run_id,
        report_path=report_path.resolve(),
        report_ref=report_ref,
        raw_run_root=raw_run_root,
        members=tuple(members),
    )


def _read_json_mapping(path: Path, *, name: str) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        raise ValueError(f"{name} is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return dict(payload)


def _validate_request_identity(
    command: GitHubRealClosedLoopSmokeCommand,
    request: Mapping[str, Any],
) -> tuple[str, ...]:
    issues: list[str] = []
    if request.get("repository") != command.repository:
        issues.append("request repository does not match smoke command")
    try:
        request_issue_number = int(request.get("issue_number", 0))
    except (TypeError, ValueError):
        request_issue_number = 0
    if request_issue_number != command.issue_number:
        issues.append("request issue_number does not match smoke command")
    return tuple(issues)


def _select_required_member_bytes(
    members: Sequence[GitHubDualArtifactRunMember],
) -> dict[str, bytes | None]:
    selected: dict[str, bytes | None] = {
        "request": None,
        "advisory": None,
        "manifest": None,
    }
    for member in members:
        if member.filename == "authoritative_request.json":
            selected["request"] = member.content
        elif member.filename == "copilot_advisory.json":
            selected["advisory"] = member.content
        elif member.filename == "dual_artifact_manifest.json":
            selected["manifest"] = member.content
    return selected


def _result(
    command: GitHubRealClosedLoopSmokeCommand,
    *,
    issues: Sequence[str],
    assembly: Mapping[str, Any] | None = None,
    laboratory_projection: Mapping[str, Any] | None = None,
    publication_preview: Mapping[str, Any] | None = None,
    publication_plan: Mapping[str, Any] | None = None,
) -> GitHubRealClosedLoopSmokeResult:
    normalized = tuple(
        dict.fromkeys(str(issue) for issue in issues if str(issue))
    )
    return GitHubRealClosedLoopSmokeResult(
        valid=not normalized,
        issues=normalized,
        repository=command.repository,
        run_id=command.run_id,
        issue_number=command.issue_number,
        run_group_report_ref=command.run_group_report_ref,
        assembly=dict(assembly or {}),
        laboratory_projection=dict(laboratory_projection or {}),
        publication_preview=dict(publication_preview or {}),
        publication_plan=dict(publication_plan or {}),
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _required_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value.strip()


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


__all__ = (
    "DEFAULT_DOCUMENT_KINDS",
    "DEFAULT_SPECIALIST_REFS",
    "SCHEMA",
    "GitHubRealClosedLoopSmokeCommand",
    "GitHubRealClosedLoopSmokeResult",
    "ImportedGitHubRunBundle",
    "build_real_closed_loop_laboratory_command",
    "load_imported_github_run_bundle",
    "run_github_real_closed_loop_smoke",
)
