#!/usr/bin/env python3
"""Import one real Actions run, execute r14 on declared real ports, and preview.

The command downloads exactly three correlated artifacts, loads an explicit
existing-runtime factory, executes the already-closed r14 composition, writes a
reusable r14 JSON file, then performs the r15-r1 remote publication preview.  It
never performs a remote mutation and contains no fallback dummy backend.
"""

from __future__ import annotations

import argparse
import asyncio
import configparser
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from context.github_dual_artifact_run_assembly_0281 import (  # noqa: E402
    GitHubDualArtifactRunAssemblyCommand,
    GitHubDualArtifactRunAssemblyPolicy,
    GitHubDualArtifactRunMember,
    run_github_dual_artifact_run_assembly,
)
from context.love_final_deliverable_remote_publication_0287 import (  # noqa: E402
    LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_COMMAND_SCHEMA,
    LoveFinalDeliverableRemotePublicationCommand,
    execute_love_final_deliverable_remote_publication,
)
from context.love_full_deterministic_local_smoke_0287 import (  # noqa: E402
    LOVE_FULL_DETERMINISTIC_LOCAL_SMOKE_COMMAND_SCHEMA,
    LoveFullDeterministicLocalSmokeCommand,
    run_love_full_deterministic_local_smoke,
)
from context.love_imported_actions_runtime_contract_0287 import (  # noqa: E402
    ImportedActionsRuntimeLease,
    ImportedActionsRuntimeContractError,
    ImportedActionsRuntimeFactory,
    acquire_imported_actions_runtime_lease,
    validate_imported_actions_runtime_ports,
)
from context.human_readable_artifact_identity_0287 import (  # noqa: E402
    matches_actions_artifact_name,
)
from context.love_actions_closed_loop_resolution_0287 import (  # noqa: E402
    LoveActionsClosedLoopResolutionError,
    LoveProjectV2TargetRequest,
)
from context.love_imported_actions_run_preview_0287 import (  # noqa: E402
    GitHubActionsArtifactIdentity,
    LOVE_IMPORTED_ACTIONS_RUN_PREVIEW_COMMAND_SCHEMA,
    LoveImportedActionsRunPreviewCommand,
    correlate_imported_actions_run_preview,
)
from context.source_candidate import SourceCandidateDecision  # noqa: E402
from publish_love_final_deliverable_0287 import (  # noqa: E402
    GitHubCliFinalDeliverablePublicationAdapter,
)

_EXPECTED_ARTIFACTS = {
    "autodoc-authoritative-request": "authoritative_request.json",
    "autodoc-copilot-advisory": "copilot_advisory.json",
    "autodoc-dual-artifact-manifest": "dual_artifact_manifest.json",
}


class LoveActionsClosedLoopPreviewError(RuntimeError):
    """Raised when import, local execution or preview fails closed."""


@dataclass(frozen=True, slots=True)
class LoveActionsClosedLoopPreviewCliCommand:
    """Typed CLI intention for one imported-run preview."""

    repository: str
    run_id: str
    project_owner: str
    project_number: int
    project_item_id: str
    project_field_ref: str
    project_field_name: str
    project_status_value: str
    output_path: Path
    gh_command: str
    token_env: str
    context_generation: int
    branch_ref: str
    project_ref: str
    security_scope: str
    artifact_storage_ref: str
    policy_decision_id: str
    candidate_decision: str
    target_context_id: str
    operator_reason: str
    runtime_factory_ref: str

    def __post_init__(self) -> None:
        for name in (
            "repository",
            "run_id",
            "project_owner",
            "project_field_name",
            "project_status_value",
            "gh_command",
            "token_env",
            "branch_ref",
            "project_ref",
            "security_scope",
            "artifact_storage_ref",
            "policy_decision_id",
            "operator_reason",
            "runtime_factory_ref",
        ):
            if not str(getattr(self, name)).strip():
                raise LoveActionsClosedLoopPreviewError(
                    f"{name} must be non-empty"
                )
        if "/" not in self.repository:
            raise LoveActionsClosedLoopPreviewError(
                "repository must use owner/name"
            )
        if self.project_number <= 0:
            raise LoveActionsClosedLoopPreviewError(
                "project_number must be positive"
            )
        override_presence = (
            bool(self.project_item_id.strip()),
            bool(self.project_field_ref.strip()),
        )
        if override_presence.count(True) == 1:
            raise LoveActionsClosedLoopPreviewError(
                "project item and field overrides must be supplied together"
            )
        if self.context_generation < 0:
            raise LoveActionsClosedLoopPreviewError(
                "context_generation must be non-negative"
            )
        if self.candidate_decision not in {"promote", "merge"}:
            raise LoveActionsClosedLoopPreviewError(
                "candidate_decision must be promote or merge"
            )
        if self.candidate_decision == "merge" and not self.target_context_id.strip():
            raise LoveActionsClosedLoopPreviewError(
                "merge candidate decision requires target_context_id"
            )
        if ":" not in self.runtime_factory_ref:
            raise LoveActionsClosedLoopPreviewError(
                "runtime_factory_ref must use module:function"
            )
        if not self.branch_ref.startswith("context-branch:"):
            raise LoveActionsClosedLoopPreviewError(
                "branch_ref must be typed"
            )
        if not self.project_ref.startswith("project:"):
            raise LoveActionsClosedLoopPreviewError(
                "project_ref must be typed"
            )
        if not self.security_scope.startswith("scope:"):
            raise LoveActionsClosedLoopPreviewError(
                "security_scope must be typed"
            )
        if not self.artifact_storage_ref.startswith("storage:"):
            raise LoveActionsClosedLoopPreviewError(
                "artifact_storage_ref must be typed"
            )
        if not self.policy_decision_id.startswith("policy:"):
            raise LoveActionsClosedLoopPreviewError(
                "policy_decision_id must be typed"
            )


@dataclass(frozen=True, slots=True)
class LoveClosedLoopLocalSettings:
    """One-time local integration settings resolved before the run import."""

    project_owner: str
    project_number: int
    project_field_name: str
    project_status_value: str
    runtime_factory_ref: str
    token_env: str

    def __post_init__(self) -> None:
        if not self.project_owner.strip():
            raise LoveActionsClosedLoopPreviewError(
                "ProjectV2 owner is not configured"
            )
        if self.project_number <= 0:
            raise LoveActionsClosedLoopPreviewError(
                "ProjectV2 number is not configured"
            )
        if not self.project_field_name.strip():
            raise LoveActionsClosedLoopPreviewError(
                "ProjectV2 field name is not configured"
            )
        if not self.project_status_value.strip():
            raise LoveActionsClosedLoopPreviewError(
                "ProjectV2 status value is not configured"
            )
        if ":" not in self.runtime_factory_ref:
            raise LoveActionsClosedLoopPreviewError(
                "real runtime factory is not configured; set [runtime] factory "
                "in .var/config/love_actions_closed_loop.ini or export "
                "AUTODOC_LOVE_RUNTIME_FACTORY=module:function"
            )
        if not self.token_env.strip():
            raise LoveActionsClosedLoopPreviewError(
                "GitHub token environment name is not configured"
            )


class GitHubCliActionsRunAdapter:
    """Read/download adapter for one GitHub Actions run."""

    def __init__(self, *, gh_command: str, token_env: str) -> None:
        self._gh_command = gh_command
        self._env = os.environ.copy()
        token = self._env.get(token_env, "").strip()
        if token:
            self._env["GH_TOKEN"] = token

    def read_run(self, repository: str, run_id: str) -> Mapping[str, Any]:
        return _mapping(
            self._run_json(
                ["api", f"repos/{repository}/actions/runs/{run_id}"]
            ),
            "Actions run",
        )

    def list_artifacts(
        self,
        repository: str,
        run_id: str,
    ) -> tuple[Mapping[str, Any], ...]:
        payload = self._run_json(
            [
                "api",
                "--paginate",
                "--slurp",
                (
                    f"repos/{repository}/actions/runs/{run_id}/artifacts"
                    "?per_page=100"
                ),
            ]
        )
        pages = payload if isinstance(payload, list) else [payload]
        artifacts: list[Mapping[str, Any]] = []
        for page in pages:
            if not isinstance(page, Mapping):
                continue
            raw_artifacts = page.get("artifacts", ())
            if not isinstance(raw_artifacts, Sequence) or isinstance(
                raw_artifacts,
                (str, bytes, bytearray),
            ):
                continue
            artifacts.extend(
                item for item in raw_artifacts if isinstance(item, Mapping)
            )
        return tuple(artifacts)

    def download_artifact(
        self,
        *,
        repository: str,
        run_id: str,
        artifact_name: str,
        destination: Path,
    ) -> None:
        destination.mkdir(parents=True, exist_ok=True)
        self._run(
            [
                "run",
                "download",
                run_id,
                "--repo",
                repository,
                "--name",
                artifact_name,
                "--dir",
                str(destination),
            ]
        )

    def _run_json(self, arguments: Sequence[str]) -> Any:
        completed = self._run(arguments)
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise LoveActionsClosedLoopPreviewError(
                "GitHub CLI returned invalid JSON"
            ) from exc

    def _run(self, arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [self._gh_command, *arguments],
            text=True,
            capture_output=True,
            check=False,
            env=self._env,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise LoveActionsClosedLoopPreviewError(
                f"GitHub CLI command failed ({completed.returncode}): {detail}"
            )
        return completed


def execute_love_actions_closed_loop_preview(
    command: LoveActionsClosedLoopPreviewCliCommand,
    *,
    actions_adapter: GitHubCliActionsRunAdapter,
    publication_adapter: GitHubCliFinalDeliverablePublicationAdapter,
    runtime_factory: ImportedActionsRuntimeFactory,
) -> Mapping[str, Any]:
    """Import, execute locally, preview remotely and atomically persist JSON."""

    run = actions_adapter.read_run(command.repository, command.run_id)
    status = str(run.get("status", ""))
    conclusion = str(run.get("conclusion", ""))
    if status != "completed" or conclusion != "success":
        raise LoveActionsClosedLoopPreviewError(
            f"Actions run must be completed/success, got {status}/{conclusion}"
        )
    if str(run.get("id", "")) != command.run_id:
        raise LoveActionsClosedLoopPreviewError(
            "Actions run identity differs from requested run_id"
        )
    run_repository = run.get("repository")
    if isinstance(run_repository, Mapping):
        full_name = str(run_repository.get("full_name", "")).strip()
        if full_name and full_name != command.repository:
            raise LoveActionsClosedLoopPreviewError(
                "Actions run repository differs from requested repository"
            )
    workflow_name = str(run.get("name", "")).strip()
    created_at = str(run.get("created_at", "")).strip()
    if not workflow_name or not created_at:
        raise LoveActionsClosedLoopPreviewError(
            "Actions run metadata is incomplete"
        )

    artifact_metadata = _select_artifacts(
        actions_adapter.list_artifacts(command.repository, command.run_id),
        run_id=command.run_id,
    )
    with tempfile.TemporaryDirectory(
        prefix=f"autodoc-love-run-{command.run_id}-"
    ) as temp_dir:
        root = Path(temp_dir)
        members: list[GitHubDualArtifactRunMember] = []
        identities: list[GitHubActionsArtifactIdentity] = []
        request_payload: Mapping[str, Any] | None = None
        for artifact_name, filename in _EXPECTED_ARTIFACTS.items():
            metadata = artifact_metadata[artifact_name]
            actual_artifact_name = str(metadata.get("name", "")).strip()
            destination = root / artifact_name
            actions_adapter.download_artifact(
                repository=command.repository,
                run_id=command.run_id,
                artifact_name=actual_artifact_name,
                destination=destination,
            )
            path = _find_exact_download(destination, filename)
            content = path.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            members.append(
                GitHubDualArtifactRunMember(
                    artifact_name=artifact_name,
                    filename=filename,
                    content=content,
                )
            )
            identities.append(
                GitHubActionsArtifactIdentity(
                    artifact_id=int(metadata["id"]),
                    artifact_name=actual_artifact_name,
                    filename=filename,
                    archive_size_in_bytes=int(
                        metadata.get("size_in_bytes", 0)
                    ),
                    content_size_in_bytes=len(content),
                    content_digest=digest,
                    created_at=str(metadata.get("created_at", created_at)),
                    expired=bool(metadata.get("expired", False)),
                )
            )
            if artifact_name == "autodoc-authoritative-request":
                request_payload = _mapping(
                    json.loads(content.decode("utf-8")),
                    "authoritative request",
                )

    if request_payload is None:
        raise LoveActionsClosedLoopPreviewError(
            "authoritative request was not loaded"
        )
    preflight_assembly = run_github_dual_artifact_run_assembly(
        GitHubDualArtifactRunAssemblyCommand(
            repository=command.repository,
            run_id=command.run_id,
            members=tuple(members),
        ),
        GitHubDualArtifactRunAssemblyPolicy(allow_missing_advisory=False),
    )
    if not preflight_assembly.valid:
        raise LoveActionsClosedLoopPreviewError(
            "Actions artifact preflight failed: "
            + "; ".join(preflight_assembly.issues)
        )
    validated_request = _mapping(
        _mapping(preflight_assembly.intake, "preflight intake").get("request"),
        "validated authoritative request",
    )
    issue_number = int(validated_request.get("issue_number", 0))
    if issue_number <= 0:
        raise LoveActionsClosedLoopPreviewError(
            "validated authoritative request issue_number is invalid"
        )

    project_target = publication_adapter.resolve_project_target(
        LoveProjectV2TargetRequest(
            repository=command.repository,
            issue_number=issue_number,
            project_owner=command.project_owner,
            project_number=command.project_number,
            field_name=command.project_field_name,
            project_item_id_override=command.project_item_id,
            field_ref_override=command.project_field_ref,
        )
    )

    runtime_lease = _acquire_imported_actions_runtime_lease(
        runtime_factory(
            repository=command.repository,
            run_id=command.run_id,
            request_payload=dict(validated_request),
            runtime_context={
                "run_assembly": preflight_assembly.to_mapping(),
                "branch_ref": command.branch_ref,
                "project_ref": command.project_ref,
                "security_scope": command.security_scope,
                "artifact_storage_ref": command.artifact_storage_ref,
                "policy_decision_id": command.policy_decision_id,
            },
            created_at=created_at,
        )
    )
    runtime = runtime_lease.ports
    try:
        r14_command = LoveFullDeterministicLocalSmokeCommand(
            schema=LOVE_FULL_DETERMINISTIC_LOCAL_SMOKE_COMMAND_SCHEMA,
            repository=command.repository,
            run_id=command.run_id,
            members=tuple(members),
            operator_decision=SourceCandidateDecision(
                action=command.candidate_decision,
                reason=command.operator_reason,
                target_context_id=(
                    command.target_context_id
                    if command.candidate_decision == "merge"
                    else None
                ),
            ),
            conversation_ref=(
                f"laboratory-conversation:actions-run-{command.run_id}"
            ),
            return_route_ref=f"route:github-issue-{issue_number}",
            context_generation=command.context_generation,
            base_revision_ref=runtime.base_revision_ref,
            branch_ref=command.branch_ref,
            project_ref=command.project_ref,
            security_scope=command.security_scope,
            artifact_storage_ref=command.artifact_storage_ref,
            created_at=created_at,
            policy_decision_id=command.policy_decision_id,
            project_item_id=project_target.project_item_id,
            project_field_ref=project_target.field_ref,
            project_field_name=project_target.field_name,
            project_status_value=command.project_status_value,
            context_refs=(f"ctx:github-actions-run:{command.run_id}",),
            evidence_refs=(f"evidence:github-actions-run:{command.run_id}",),
        )
        r14_result = asyncio.run(
            _run_r14_on_existing_scheduler(
                r14_command,
                runtime,
                runtime_lease=runtime_lease,
            )
        )
    except BaseException:
        _close_tool_bounded_runtime_lease(runtime, runtime_lease)
        raise
    r14_mapping = r14_result.to_mapping()

    preview_command = LoveFinalDeliverableRemotePublicationCommand(
        schema=LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_COMMAND_SCHEMA,
        plan=r14_result.publication_plan,
        operator_decision="approve",
        execute=False,
        confirm_plan_digest="",
        remote_mutation_allowed=False,
        issue_publication_allowed=False,
        project_projection_allowed=False,
    )
    preview = execute_love_final_deliverable_remote_publication(
        preview_command,
        issue_port=publication_adapter,
        project_port=publication_adapter,
    )
    preview_mapping = preview.to_mapping()
    if not preview.valid or preview.mode != "preview":
        raise LoveActionsClosedLoopPreviewError(
            "remote publication preview failed: "
            + "; ".join(preview.issues)
        )

    correlated = correlate_imported_actions_run_preview(
        LoveImportedActionsRunPreviewCommand(
            schema=LOVE_IMPORTED_ACTIONS_RUN_PREVIEW_COMMAND_SCHEMA,
            repository=command.repository,
            run_id=command.run_id,
            workflow_name=workflow_name,
            workflow_conclusion=conclusion,
            artifacts=tuple(identities),
            runtime_attestation=runtime.attestation,
        ),
        r14_result=r14_mapping,
        publication_preview=preview_mapping,
    )
    if not correlated.valid:
        raise LoveActionsClosedLoopPreviewError(
            "imported-run correlation failed: "
            + "; ".join(correlated.issues)
        )
    output = correlated.to_mapping()
    output["_r15_resolution"] = project_target.to_mapping()
    output["_r15_runtime_lease"] = runtime_lease.to_readback_mapping()
    _write_json_atomic(command.output_path, output)
    return output


async def _run_r14_on_existing_scheduler(
    command: LoveFullDeterministicLocalSmokeCommand,
    runtime: Any,
    *,
    runtime_lease: ImportedActionsRuntimeLease | None = None,
) -> Any:
    """Run r14 without stealing an externally managed Scheduler lifecycle."""

    async def execute_r14() -> Any:
        return await run_love_full_deterministic_local_smoke(
            command,
            scheduler=runtime.scheduler,
            dispatcher=runtime.dispatcher,
            authority_store=runtime.authority_store,
            projection_port=runtime.projection_port,
            collection=runtime.collection,
            embedder=runtime.embedder,
            executor=runtime.executor,
        )

    if runtime.scheduler_lifecycle == "externally-managed":
        return await execute_r14()

    scheduler_task = asyncio.create_task(
        runtime.scheduler.run(),
        name=f"love-r15-r2-scheduler-{command.run_id}",
    )
    r14_task = asyncio.create_task(
        execute_r14(),
        name=f"love-r15-r2-r14-{command.run_id}",
    )
    scheduler_completion_consumed = False
    try:
        done, _ = await asyncio.wait(
            {scheduler_task, r14_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        if scheduler_task in done and not r14_task.done():
            scheduler_error = scheduler_task.exception()
            scheduler_completion_consumed = True
            r14_task.cancel()
            await asyncio.gather(r14_task, return_exceptions=True)
            if scheduler_error is not None:
                raise LoveActionsClosedLoopPreviewError(
                    "injected Scheduler failed before r14 completed"
                ) from scheduler_error
            raise LoveActionsClosedLoopPreviewError(
                "injected Scheduler stopped before r14 completed"
            )
        return await r14_task
    finally:
        try:
            if not r14_task.done():
                r14_task.cancel()
                await asyncio.gather(r14_task, return_exceptions=True)
            if not scheduler_task.done():
                await runtime.scheduler.shutdown()
            if scheduler_completion_consumed:
                await asyncio.gather(
                    scheduler_task,
                    return_exceptions=True,
                )
            else:
                try:
                    await scheduler_task
                except Exception as exc:
                    raise LoveActionsClosedLoopPreviewError(
                        "injected Scheduler failed during r14 lifecycle"
                    ) from exc
        finally:
            if runtime_lease is not None:
                _close_tool_bounded_runtime_lease(runtime, runtime_lease)


def _acquire_imported_actions_runtime_lease(
    value: object,
) -> ImportedActionsRuntimeLease:
    """Inject process identity and preserve the historical ports gate."""

    lease = acquire_imported_actions_runtime_lease(
        value,
        current_process_id=os.getpid(),
    )
    validate_imported_actions_runtime_ports(lease.ports)
    return lease


def _close_tool_bounded_runtime_lease(
    runtime: Any,
    runtime_lease: ImportedActionsRuntimeLease,
) -> None:
    """Close only resources explicitly owned by a tool-bounded runtime."""

    if runtime.scheduler_lifecycle == "tool-bounded":
        runtime_lease.close(
            current_process_id=os.getpid(),
        )


def _load_runtime_factory(reference: str) -> ImportedActionsRuntimeFactory:
    """Load one explicit ``module:function`` factory; never select a fallback."""

    module_name, separator, attribute = reference.partition(":")
    if not separator or not module_name.strip() or not attribute.strip():
        raise LoveActionsClosedLoopPreviewError(
            "runtime factory must use module:function"
        )
    try:
        module = importlib.import_module(module_name.strip())
    except ImportError as exc:
        raise LoveActionsClosedLoopPreviewError(
            f"cannot import runtime factory module {module_name}: {exc}"
        ) from exc
    factory = getattr(module, attribute.strip(), None)
    if not callable(factory):
        raise LoveActionsClosedLoopPreviewError(
            f"runtime factory is not callable: {reference}"
        )
    return factory


def _select_artifacts(
    artifacts: Sequence[Mapping[str, Any]],
    *,
    run_id: str,
) -> dict[str, Mapping[str, Any]]:
    selected: dict[str, Mapping[str, Any]] = {}
    for expected_name in _EXPECTED_ARTIFACTS:
        matches = tuple(
            item
            for item in artifacts
            if matches_actions_artifact_name(
                str(item.get("name", "")), expected_name
            )
        )
        if len(matches) != 1:
            raise LoveActionsClosedLoopPreviewError(
                "expected exactly one Actions artifact for "
                f"{expected_name} (legacy exact name or readable canonical suffix)"
            )
        item = matches[0]
        if bool(item.get("expired", False)):
            raise LoveActionsClosedLoopPreviewError(
                f"Actions artifact is expired: {expected_name}"
            )
        if int(item.get("id", 0)) <= 0:
            raise LoveActionsClosedLoopPreviewError(
                f"Actions artifact id is invalid: {expected_name}"
            )
        workflow_run = item.get("workflow_run")
        if not isinstance(workflow_run, Mapping):
            raise LoveActionsClosedLoopPreviewError(
                f"Actions artifact workflow_run is missing: {expected_name}"
            )
        if str(workflow_run.get("id", "")) != run_id:
            raise LoveActionsClosedLoopPreviewError(
                f"Actions artifact run identity mismatch: {expected_name}"
            )
        selected[expected_name] = item
    return selected


def _find_exact_download(destination: Path, filename: str) -> Path:
    matches = tuple(path for path in destination.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise LoveActionsClosedLoopPreviewError(
            f"downloaded artifact must contain exactly one {filename}"
        )
    return matches[0]


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        dict(payload),
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    ) + "\n"
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(serialized, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LoveActionsClosedLoopPreviewError(
            f"{name} must be a JSON object"
        )
    return value


def _read_ini(path: Path, *, required: bool) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    if not path.is_file():
        if required:
            raise LoveActionsClosedLoopPreviewError(
                f"configuration file not found: {path}"
            )
        return parser
    try:
        with path.open("r", encoding="utf-8") as handle:
            parser.read_file(handle)
    except (OSError, configparser.Error) as exc:
        raise LoveActionsClosedLoopPreviewError(
            f"cannot read configuration file {path}: {exc}"
        ) from exc
    return parser


def _config_value(
    parser: configparser.ConfigParser,
    section: str,
    option: str,
) -> str:
    if not parser.has_option(section, option):
        return ""
    return parser.get(section, option).strip()


def _positive_int(value: str, name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise LoveActionsClosedLoopPreviewError(
            f"{name} must be a positive integer"
        ) from exc
    if parsed <= 0:
        raise LoveActionsClosedLoopPreviewError(
            f"{name} must be a positive integer"
        )
    return parsed


def _resolve_local_settings(args: argparse.Namespace) -> LoveClosedLoopLocalSettings:
    configured_path = str(args.config or os.environ.get(
        "AUTODOC_LOVE_CLOSED_LOOP_CONFIG", ""
    )).strip()
    local_path = (
        Path(configured_path)
        if configured_path
        else _ROOT / ".var/config/love_actions_closed_loop.ini"
    )
    local = _read_ini(local_path, required=bool(configured_path))

    configured_project_path = str(args.project_config or os.environ.get(
        "AUTODOC_GITHUB_PROJECT_CONFIG", ""
    )).strip()
    project_path = (
        Path(configured_project_path)
        if configured_project_path
        else _ROOT / ".var/config/github_project_v2_query_only.ini"
    )
    project = _read_ini(
        project_path,
        required=bool(configured_project_path),
    )

    project_owner = (
        str(args.project_owner or "").strip()
        or _config_value(local, "project", "owner")
        or _config_value(project, "project", "owner")
    )
    project_number_text = (
        str(args.project_number or "").strip()
        or _config_value(local, "project", "number")
        or _config_value(project, "project", "number")
    )
    if not project_number_text:
        raise LoveActionsClosedLoopPreviewError(
            "ProjectV2 number is not configured; keep "
            ".var/config/github_project_v2_query_only.ini or pass "
            "--project-number"
        )
    project_field_name = (
        str(args.project_field_name or "").strip()
        or _config_value(local, "project", "field_name")
        or "Statut révision"
    )
    project_status_value = (
        str(args.project_status_value or "").strip()
        or _config_value(local, "project", "status_value")
        or "Terminé"
    )
    runtime_factory_ref = (
        str(args.runtime_factory or "").strip()
        or os.environ.get("AUTODOC_LOVE_RUNTIME_FACTORY", "").strip()
        or _config_value(local, "runtime", "factory")
    )
    token_env = (
        str(args.token_env or "").strip()
        or _config_value(local, "github", "token_env")
        or _config_value(project, "github", "token_env")
        or "AUTODOC_PROJECT_TOKEN"
    )
    return LoveClosedLoopLocalSettings(
        project_owner=project_owner,
        project_number=_positive_int(
            project_number_text, "ProjectV2 number"
        ),
        project_field_name=project_field_name,
        project_status_value=project_status_value,
        runtime_factory_ref=runtime_factory_ref,
        token_env=token_env,
    )


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--config")
    parser.add_argument("--project-config")
    parser.add_argument("--project-owner")
    parser.add_argument("--project-number", type=int)
    parser.add_argument("--project-item-id", default="")
    parser.add_argument("--project-field-ref", default="")
    parser.add_argument("--project-field-name")
    parser.add_argument("--project-status-value")
    parser.add_argument(
        "--runtime-factory",
        help=(
            "Advanced override for the configured real runtime factory as "
            "module:function."
        ),
    )
    parser.add_argument("--output")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument("--token-env")
    parser.add_argument("--context-generation", type=int, default=1)
    parser.add_argument(
        "--candidate-decision",
        required=True,
        choices=("promote", "merge"),
        help="Explicit SourceCandidate operator gate before the laboratory route.",
    )
    parser.add_argument("--target-context-id", default="")
    parser.add_argument("--branch-ref", default="context-branch:main")
    parser.add_argument("--project-ref")
    parser.add_argument("--security-scope", default="scope:local")
    parser.add_argument("--artifact-storage-ref")
    parser.add_argument("--policy-decision-id")
    parser.add_argument(
        "--operator-reason",
        default="Imported Actions run approved for r15-r2 preview.",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        settings = _resolve_local_settings(args)
        run_id = str(args.run_id).strip()
        repository = str(args.repository).strip()
        slug = repository.replace("/", "-")
        output_path = Path(
            args.output or f"/tmp/love-r14-result-{run_id}.json"
        )
        command = LoveActionsClosedLoopPreviewCliCommand(
            repository=repository,
            run_id=run_id,
            project_owner=settings.project_owner,
            project_number=settings.project_number,
            project_item_id=str(args.project_item_id),
            project_field_ref=str(args.project_field_ref),
            project_field_name=settings.project_field_name,
            project_status_value=settings.project_status_value,
            output_path=output_path,
            gh_command=str(args.gh_command),
            token_env=settings.token_env,
            context_generation=int(args.context_generation),
            branch_ref=str(args.branch_ref),
            project_ref=str(args.project_ref or f"project:{slug}"),
            security_scope=str(args.security_scope),
            artifact_storage_ref=str(
                args.artifact_storage_ref
                or f"storage:zfs:love-actions-run-{run_id}"
            ),
            policy_decision_id=str(
                args.policy_decision_id
                or f"policy:love-actions-run-{run_id}-preview"
            ),
            candidate_decision=str(args.candidate_decision),
            target_context_id=str(args.target_context_id),
            operator_reason=str(args.operator_reason),
            runtime_factory_ref=settings.runtime_factory_ref,
        )
        actions_adapter = GitHubCliActionsRunAdapter(
            gh_command=command.gh_command,
            token_env=command.token_env,
        )
        publication_adapter = GitHubCliFinalDeliverablePublicationAdapter(
            gh_command=command.gh_command,
            token_env=command.token_env,
        )
        runtime_factory = _load_runtime_factory(command.runtime_factory_ref)
        result = execute_love_actions_closed_loop_preview(
            command,
            actions_adapter=actions_adapter,
            publication_adapter=publication_adapter,
            runtime_factory=runtime_factory,
        )
    except (
        LoveActionsClosedLoopPreviewError,
        LoveActionsClosedLoopResolutionError,
        ImportedActionsRuntimeContractError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    import_info = _mapping(result.get("_r15_import"), "_r15_import")
    resolution = _mapping(
        result.get("_r15_resolution"), "_r15_resolution"
    )
    preview = _mapping(
        result.get("remote_publication_preview"),
        "remote_publication_preview",
    )
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"output: {output_path}")
        print(f"run_id: {import_info['run_id']}")
        print(f"project_item_id: {resolution['project_item_id']}")
        print(f"project_field_ref: {resolution['field_ref']}")
        print(f"proof_digest: {import_info['proof_digest']}")
        print(f"plan_digest: {import_info['plan_digest']}")
        print(f"preview_action: {preview.get('action')}")
        print("remote_mutation_performed: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
