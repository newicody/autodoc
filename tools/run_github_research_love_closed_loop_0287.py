#!/usr/bin/env python3
"""Run the complete GitHub research/love cycle without rebuilding infrastructure.

Two explicit modes preserve the human confirmation boundary:

``prepare``
    Load one fetched ready_run and its three local artifacts, acquire the
    already-installed runtime through an injected factory, execute the r16-r19
    local composition, persist every serializable stage and stop at the exact
    publication plan digest.

``complete``
    Reload the prepared JSON, reacquire the same installed runtime, execute the
    existing controlled Issue + ProjectV2 publication with the confirmed digest,
    then persist the r16-r18 publication evidence and close the SQL cycle.

This tool does not construct a Scheduler, Dispatcher, SQL store, Qdrant client,
OpenVINO runtime, laboratory provider or alternate GitHub transport.
"""

from __future__ import annotations

import argparse
import asyncio
from contextlib import contextmanager
from collections.abc import Callable, Iterator, Mapping, Sequence
from datetime import datetime, timezone
import importlib
import json
import os
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from context.github_research_love_complete_closed_loop_0287 import (  # noqa: E402
    GitHubResearchLoveClosedLoopPrepareCommand,
    prepare_github_research_love_closed_loop,
)
from context.github_research_love_final_remote_publication_0287 import (  # noqa: E402
    PLAN_SCHEMA as WRAPPED_PUBLICATION_PLAN_SCHEMA,
    GitHubResearchLoveFinalPublicationExecution,
    GitHubResearchLoveFinalPublicationPlan,
    execute_github_research_love_final_publication,
)
from context.github_research_love_publication_evidence_sql_0287 import (  # noqa: E402
    GitHubResearchLovePublicationEvidenceCommand,
    close_github_research_love_cycle,
)
from context.love_final_deliverable_remote_publication_0287 import (  # noqa: E402
    parse_love_final_deliverable_publication_plan,
)
from context.love_imported_actions_runtime_contract_0287 import (  # noqa: E402
    ImportedActionsRuntimeLease,
    acquire_imported_actions_runtime_lease,
)
from tools import assemble_fetched_github_research_admissibility_0287 as artifact_loader  # noqa: E402
from tools import publish_love_final_deliverable_0287 as publication_tool  # noqa: E402
from tools import resolve_github_research_project_target_0287 as project_target_tool  # noqa: E402
from tools.github_projectv2_repository_owner_adapter_0287 import (  # noqa: E402
    RepositoryOwnerGitHubCliFinalDeliverablePublicationAdapter,
)

REPORT_SCHEMA = "missipy.github.research_love_operational_closed_loop.v1"
_PREPARED_SCHEMA = "missipy.github.research_love_closed_loop_prepared.v1"
_FETCH_CYCLE_SCHEMA = "missipy.github_actions.artifact_fetch_cycle_once.v1"
_SCAN_SCHEMA = "missipy.github_actions.artifact_scan_once_live.v1"


class OperationalClosedLoopError(RuntimeError):
    """Raised when filesystem/runtime wiring cannot preserve r16 boundaries."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)

    prepare = subparsers.add_parser(
        "prepare",
        help="execute local stages and stop at publication confirmation",
    )
    prepare.add_argument("--fetch-cycle-report", type=Path, required=True)
    prepare.add_argument("--run-id", required=True)
    prepare.add_argument(
        "--runtime-factory",
        required=True,
        help="import path module:function implementing ImportedActionsRuntimeFactory",
    )
    prepare.add_argument("--runtime-config", type=Path)
    prepare.add_argument(
        "--policy-decision-id",
        required=True,
        help="typed policy reference passed to the installed runtime",
    )
    prepare.add_argument("--state-path", type=Path)
    prepare.add_argument(
        "--max-artifact-bytes",
        type=int,
        default=5 * 1024 * 1024,
    )
    prepare.add_argument("--issue-number", type=int, required=True)
    prepare.add_argument("--project-owner", required=True)
    prepare.add_argument("--project-number", type=int, required=True)
    prepare.add_argument("--project-field-name", default="Résumé")
    prepare.add_argument("--project-item-id-override", default="")
    prepare.add_argument("--project-field-ref-override", default="")
    prepare.add_argument("--gh-command", default="gh")
    prepare.add_argument("--token-env", default="AUTODOC_PROJECT_TOKEN")
    prepare.add_argument(
        "--project-status-value",
        default="Livrable final prêt",
    )
    prepare.add_argument(
        "--recall-query",
        default=(
            "Mettre en relation les concepts, affects, réciprocités, "
            "limites, contradictions et tensions relevés par les deux "
            "spécialistes."
        ),
    )
    prepare.add_argument("--conversation-ref", default="")
    prepare.add_argument("--return-route-ref", default="")
    prepare.add_argument("--context-ref", action="append", default=[])
    prepare.add_argument("--evidence-ref", action="append", default=[])
    prepare.add_argument("--dense-vector-name", default="dense_e5_v1")
    prepare.add_argument("--sparse-vector-name", default="sparse_lexical_v1")
    prepare.add_argument(
        "--security-scope",
        default="security:research-local",
    )
    prepare.add_argument("--branch-ref", default="branch:github-research")
    prepare.add_argument("--project-ref", default="project:github-research")
    prepare.add_argument("--created-at")
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument(
        "--format",
        choices=("json", "summary"),
        default="summary",
    )

    complete = subparsers.add_parser(
        "complete",
        help="publish the prepared plan and close the SQL cycle",
    )
    complete.add_argument("--prepared-report", type=Path, required=True)
    complete.add_argument("--confirm-plan-digest", required=True)
    complete.add_argument(
        "--runtime-factory",
        required=True,
        help="same installed runtime factory used for prepare",
    )
    complete.add_argument("--runtime-config", type=Path)
    complete.add_argument("--gh-command", default="gh")
    complete.add_argument("--token-env", default="AUTODOC_PROJECT_TOKEN")
    complete.add_argument("--closed-at")
    complete.add_argument("--output", type=Path, required=True)
    complete.add_argument(
        "--format",
        choices=("json", "summary"),
        default="summary",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(
        tuple(sys.argv[1:] if argv is None else argv)
    )
    try:
        if args.mode == "prepare":
            payload = _run_prepare(args)
        else:
            payload = _run_complete(args)
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        payload = {
            "schema": REPORT_SCHEMA,
            "valid": False,
            "mode": args.mode,
            "status": "failed",
            "issues": [f"{type(exc).__name__}: {exc}"],
            "boundaries": _common_boundaries(),
        }

    _write_json_atomic(_absolute_output(args.output), payload)
    _emit(payload, args.format)
    return 0 if payload.get("valid") is True else 2


def _run_prepare(args: argparse.Namespace) -> dict[str, Any]:
    created_at = _utc_timestamp(args.created_at)
    ready_run, artifact_contents = _load_one_fetched_ready_run(
        fetch_cycle_report=args.fetch_cycle_report,
        run_id=str(args.run_id),
        state_path=args.state_path,
        max_artifact_bytes=int(args.max_artifact_bytes),
    )
    repository = _required_text(ready_run, "repository")
    run_id = _required_text(ready_run, "run_id")
    project_target = _resolve_prepare_project_target(
        args=args,
        repository=repository,
    )
    runtime_context = {
        "schema": "missipy.github.research_love_operational_runtime_context.v1",
        "mode": "prepare",
        "policy_decision_id": _policy_decision_id(
            args.policy_decision_id
        ),
        "fetch_cycle_report": str(
            _absolute_input(args.fetch_cycle_report)
        ),
        "runtime_config": (
            ""
            if args.runtime_config is None
            else str(_absolute_input(args.runtime_config))
        ),
        "output": str(_absolute_output(args.output)),
        "project_item_id": project_target["project_item_id"],
        "project_field_ref": project_target["project_field_ref"],
        "project_target_resolution": project_target["target"],
        "filesystem_adapter": (
            "tools.assemble_fetched_github_research_admissibility_0287"
        ),
    }

    with _runtime_config_scope(args.runtime_config):
        lease = _acquire_runtime(
            factory_path=str(args.runtime_factory),
            repository=repository,
            run_id=run_id,
            request_payload=ready_run,
            runtime_context=runtime_context,
            created_at=created_at,
        )
    prepared = None
    close_payload: Mapping[str, Any] | None = None
    try:
        reference_point_reader = lease.ports.projection_port
        if not callable(
            getattr(
                reference_point_reader,
                "read_named_reference_point",
                None,
            )
        ):
            raise OperationalClosedLoopError(
                "installed projection port does not expose "
                "reference-only Qdrant readback"
            )

        prepared = asyncio.run(
            prepare_github_research_love_closed_loop(
                GitHubResearchLoveClosedLoopPrepareCommand(
                    runtime_ports=lease.ports,
                    ready_run=ready_run,
                    artifact_contents=artifact_contents,
                    reference_point_reader=reference_point_reader,
                    requested_at=created_at,
                    analysis_created_at=created_at,
                    projected_at=created_at,
                    final_created_at=created_at,
                    recall_query_text=str(args.recall_query),
                    project_item_id=project_target[
                        "project_item_id"
                    ],
                    project_field_ref=project_target[
                        "project_field_ref"
                    ],
                    project_field_name=project_target[
                        "project_field_name"
                    ],
                    project_status_value=str(args.project_status_value),
                    conversation_ref=str(args.conversation_ref),
                    return_route_ref=str(args.return_route_ref),
                    context_refs=tuple(args.context_ref),
                    evidence_refs=tuple(args.evidence_ref),
                    dense_vector_name=str(args.dense_vector_name),
                    sparse_vector_name=str(args.sparse_vector_name),
                    security_scope=str(args.security_scope),
                    branch_ref=str(args.branch_ref),
                    project_ref=str(args.project_ref),
                )
            )
        )
    finally:
        close_payload = _close_runtime_lease(lease)

    if prepared is None:
        raise OperationalClosedLoopError(
            "local closed-loop preparation produced no result"
        )
    prepared_mapping = prepared.to_mapping()
    valid = prepared.valid
    return {
        "schema": REPORT_SCHEMA,
        "valid": valid,
        "mode": "prepare",
        "status": prepared.status,
        "issues": list(prepared.issues),
        "input": {
            "repository": repository,
            "run_id": run_id,
            "ready_run": dict(ready_run),
            "fetch_cycle_report": str(
                _absolute_input(args.fetch_cycle_report)
            ),
            "created_at": created_at,
            "policy_decision_id": runtime_context[
                "policy_decision_id"
            ],
            "runtime_factory": str(args.runtime_factory),
            "runtime_config": runtime_context["runtime_config"],
            "project_target": project_target,
        },
        "prepared": prepared_mapping,
        "publication_plan_digest": (
            prepared.publication_plan.plan_digest if valid else ""
        ),
        "runtime_close": close_payload,
        "next_command": (
            "complete --prepared-report <this-file> "
            "--confirm-plan-digest <publication_plan_digest>"
            if valid
            else ""
        ),
        "boundaries": {
            **_common_boundaries(),
            "local_artifact_files_read": True,
            "project_target_resolved_read_only": True,
            "existing_complete_composition_reused": True,
            "remote_publication_performed": False,
            "cycle_closed": False,
            "operator_confirmation_required": valid,
        },
    }


def _run_complete(args: argparse.Namespace) -> dict[str, Any]:
    report_path = _absolute_input(args.prepared_report)
    prepared_report = _read_mapping(report_path, "prepared report")
    _validate_prepared_report(prepared_report)

    input_mapping = _required_mapping(prepared_report, "input")
    prepared_mapping = _required_mapping(prepared_report, "prepared")
    stages = _required_mapping(prepared_mapping, "stages")
    final_deliverable = _required_mapping(
        stages,
        "final_deliverable_sql",
    )
    wrapped_plan_mapping = _required_mapping(
        stages,
        "publication_plan",
    )
    repository = _required_text(input_mapping, "repository")
    run_id = _required_text(input_mapping, "run_id")
    ready_run = _required_mapping(input_mapping, "ready_run")
    closed_at = _utc_timestamp(args.closed_at)

    expected_digest = _required_text(
        prepared_report,
        "publication_plan_digest",
    )
    if str(args.confirm_plan_digest) != expected_digest:
        raise OperationalClosedLoopError(
            "confirm-plan-digest mismatch"
        )

    runtime_context = {
        "schema": "missipy.github.research_love_operational_runtime_context.v1",
        "mode": "complete",
        "policy_decision_id": _policy_decision_id(
            _required_text(input_mapping, "policy_decision_id")
        ),
        "prepared_report": str(report_path),
        "runtime_config": (
            ""
            if args.runtime_config is None
            else str(_absolute_input(args.runtime_config))
        ),
        "output": str(_absolute_output(args.output)),
        "publication_plan_digest": expected_digest,
    }
    with _runtime_config_scope(args.runtime_config):
        lease = _acquire_runtime(
            factory_path=str(args.runtime_factory),
            repository=repository,
            run_id=run_id,
            request_payload=ready_run,
            runtime_context=runtime_context,
            created_at=closed_at,
        )

    remote = None
    closure = None
    close_payload: Mapping[str, Any] | None = None
    try:
        wrapped_plan = _publication_plan_from_mapping(
            wrapped_plan_mapping
        )
        if wrapped_plan.plan_digest != expected_digest:
            raise OperationalClosedLoopError(
                "prepared publication plan digest changed"
            )

        adapter = RepositoryOwnerGitHubCliFinalDeliverablePublicationAdapter(
            gh_command=str(args.gh_command),
            token_env=str(args.token_env),
        )
        remote = execute_github_research_love_final_publication(
            GitHubResearchLoveFinalPublicationExecution(
                plan=wrapped_plan,
                operator_decision="approve",
                execute=True,
                confirm_plan_digest=expected_digest,
                remote_mutation_allowed=publication_tool._env_flag(  # noqa: SLF001
                    publication_tool._REMOTE_MUTATION_ENV  # noqa: SLF001
                ),
                issue_publication_allowed=publication_tool._env_flag(  # noqa: SLF001
                    publication_tool._ISSUE_PUBLICATION_ENV  # noqa: SLF001
                ),
                project_projection_allowed=publication_tool._env_flag(  # noqa: SLF001
                    publication_tool._PROJECT_PROJECTION_ENV  # noqa: SLF001
                ),
            ),
            issue_port=adapter,
            project_port=adapter,
        )
        if not remote.valid or remote.status not in {
            "published",
            "published-replay",
        }:
            return {
                "schema": REPORT_SCHEMA,
                "valid": False,
                "mode": "complete",
                "status": "remote-publication-failed",
                "issues": list(remote.remote_result.issues),
                "input": {
                    "repository": repository,
                    "run_id": run_id,
                    "prepared_report": str(report_path),
                    "publication_plan_digest": expected_digest,
                },
                "remote_publication": remote.to_mapping(),
                "closure": None,
                "runtime_close": None,
                "boundaries": {
                    **_common_boundaries(),
                    "remote_publication_attempted": True,
                    "publication_evidence_persisted": False,
                    "cycle_closed": False,
                },
            }

        closure = close_github_research_love_cycle(
            GitHubResearchLovePublicationEvidenceCommand(
                runtime_ports=lease.ports,
                final_deliverable=final_deliverable,
                remote_publication=remote.to_mapping(),
                closed_at=closed_at,
            )
        )
    finally:
        close_payload = _close_runtime_lease(lease)

    if remote is None or closure is None:
        raise OperationalClosedLoopError(
            "complete mode did not produce publication and closure results"
        )
    return {
        "schema": REPORT_SCHEMA,
        "valid": closure.valid,
        "mode": "complete",
        "status": closure.status,
        "issues": list(closure.issues),
        "input": {
            "repository": repository,
            "run_id": run_id,
            "prepared_report": str(report_path),
            "publication_plan_digest": expected_digest,
            "closed_at": closed_at,
        },
        "remote_publication": remote.to_mapping(),
        "closure": closure.to_mapping(),
        "runtime_close": close_payload,
        "boundaries": {
            **_common_boundaries(),
            "prepared_local_stages_recomputed": False,
            "existing_remote_publication_reused": True,
            "publication_evidence_persisted": closure.valid,
            "cycle_closed": closure.valid,
            "remote_publication_reexecuted_by_closure": False,
        },
    }


def _resolve_prepare_project_target(
    *,
    args: argparse.Namespace,
    repository: str,
) -> dict[str, Any]:
    result = project_target_tool.resolve_project_target_report(
        repository=repository,
        issue_number=int(args.issue_number),
        project_owner=str(args.project_owner),
        project_number=int(args.project_number),
        field_name=str(args.project_field_name),
        project_item_id_override=str(
            args.project_item_id_override
        ),
        field_ref_override=str(
            args.project_field_ref_override
        ),
        gh_command=str(args.gh_command),
        token_env=str(args.token_env),
    )
    if result.get("valid") is not True:
        issues = result.get("issues")
        if isinstance(issues, list):
            detail = "; ".join(str(item) for item in issues)
        else:
            detail = "project target resolution failed"
        raise OperationalClosedLoopError(detail)
    return {
        "schema": result.get("schema"),
        "status": result.get("status"),
        "project_item_id": _required_text(
            result,
            "project_item_id",
        ),
        "project_field_ref": _required_text(
            result,
            "project_field_ref",
        ),
        "project_field_name": _required_text(
            result,
            "project_field_name",
        ),
        "target": dict(
            _required_mapping(result, "target")
        ),
        "boundaries": dict(
            _required_mapping(result, "boundaries")
        ),
    }


def _load_one_fetched_ready_run(
    *,
    fetch_cycle_report: Path,
    run_id: str,
    state_path: Path | None,
    max_artifact_bytes: int,
) -> tuple[dict[str, Any], tuple[Any, ...]]:
    if max_artifact_bytes <= 0:
        raise OperationalClosedLoopError(
            "max-artifact-bytes must be > 0"
        )
    normalized_run_id = run_id.strip()
    if not normalized_run_id:
        raise OperationalClosedLoopError("run-id must not be empty")

    report_path = _absolute_input(fetch_cycle_report)
    issues: list[str] = []
    cycle = artifact_loader._read_json_mapping(  # noqa: SLF001
        report_path,
        "fetch cycle report",
        issues,
    )
    if cycle.get("schema") != _FETCH_CYCLE_SCHEMA:
        issues.append("fetch cycle report schema mismatch")
    if cycle.get("valid") is not True:
        issues.append("fetch cycle report must be valid")
    if cycle.get("mode") != "execute":
        issues.append("fetch cycle report must come from execute mode")
    if cycle.get("status") != "artifacts-fetched":
        issues.append("fetch cycle status must be artifacts-fetched")

    scan_path = artifact_loader._scan_report_path(  # noqa: SLF001
        cycle,
        report_path,
        issues,
    )
    scan = (
        artifact_loader._read_json_mapping(  # noqa: SLF001
            scan_path,
            "artifact scan report",
            issues,
        )
        if scan_path is not None
        else {}
    )
    if scan and scan.get("schema") != _SCAN_SCHEMA:
        issues.append("artifact scan report schema mismatch")
    if scan and scan.get("valid") is not True:
        issues.append("artifact scan report must be valid")

    resolved_state = artifact_loader._resolve_state_path(  # noqa: SLF001
        state_path,
        scan,
        report_path,
    )
    state = (
        artifact_loader._read_json_mapping(  # noqa: SLF001
            resolved_state,
            "artifact fetch state",
            issues,
        )
        if resolved_state is not None and resolved_state.is_file()
        else {}
    )
    ready_runs = artifact_loader._ready_runs(  # noqa: SLF001
        cycle,
        scan,
        (normalized_run_id,),
        issues,
    )
    if len(ready_runs) != 1:
        issues.append(
            f"expected exactly one selected ready_run, found {len(ready_runs)}"
        )
    if issues:
        raise OperationalClosedLoopError("; ".join(issues))

    ready_run = dict(ready_runs[0])
    loaded, load_issues = artifact_loader._load_ready_run_contents(  # noqa: SLF001
        ready_run,
        state=state,
        max_artifact_bytes=max_artifact_bytes,
    )
    if load_issues:
        raise OperationalClosedLoopError("; ".join(load_issues))
    if len(loaded) != 3:
        raise OperationalClosedLoopError(
            f"expected three artifact contents, found {len(loaded)}"
        )
    return ready_run, tuple(loaded)


def _acquire_runtime(
    *,
    factory_path: str,
    repository: str,
    run_id: str,
    request_payload: Mapping[str, Any],
    runtime_context: Mapping[str, Any],
    created_at: str,
) -> ImportedActionsRuntimeLease:
    factory = _load_callable(factory_path)
    produced = factory(
        repository=repository,
        run_id=run_id,
        request_payload=request_payload,
        runtime_context=runtime_context,
        created_at=created_at,
    )
    return acquire_imported_actions_runtime_lease(
        produced,
        current_process_id=os.getpid(),
    )


def _close_runtime_lease(
    lease: ImportedActionsRuntimeLease,
) -> Mapping[str, Any]:
    receipt = lease.close(current_process_id=os.getpid())
    return {
        "lease": lease.to_readback_mapping(),
        "receipt": receipt.to_mapping(),
    }


def _publication_plan_from_mapping(
    value: Mapping[str, Any],
) -> GitHubResearchLoveFinalPublicationPlan:
    if value.get("schema") != WRAPPED_PUBLICATION_PLAN_SCHEMA:
        raise OperationalClosedLoopError(
            "unsupported wrapped publication plan schema"
        )
    canonical = parse_love_final_deliverable_publication_plan(value)
    return GitHubResearchLoveFinalPublicationPlan(
        schema=WRAPPED_PUBLICATION_PLAN_SCHEMA,
        work_package_ref=_required_text(value, "work_package_ref"),
        final_sql_plan_digest=_required_text(
            value,
            "final_sql_plan_digest",
        ),
        final_sql_revision_ref=_required_text(
            value,
            "final_sql_revision_ref",
        ),
        final_authority_object_ref=_required_text(
            value,
            "final_authority_object_ref",
        ),
        final_artifact_ref=_required_text(value, "final_artifact_ref"),
        final_packet_ref=_required_text(value, "final_packet_ref"),
        liaison_plan_digest=_required_text(
            value,
            "liaison_plan_digest",
        ),
        publication_plan=canonical,
    )


def _validate_prepared_report(value: Mapping[str, Any]) -> None:
    if value.get("schema") != REPORT_SCHEMA:
        raise OperationalClosedLoopError(
            "unsupported prepared operational report schema"
        )
    if value.get("valid") is not True:
        raise OperationalClosedLoopError(
            "prepared operational report must be valid"
        )
    if value.get("mode") != "prepare":
        raise OperationalClosedLoopError(
            "prepared report must come from prepare mode"
        )
    if value.get("status") != "publication-confirmation-required":
        raise OperationalClosedLoopError(
            "prepared report is not awaiting publication confirmation"
        )
    prepared = _required_mapping(value, "prepared")
    if prepared.get("schema") != _PREPARED_SCHEMA:
        raise OperationalClosedLoopError(
            "embedded prepared result schema mismatch"
        )
    if prepared.get("valid") is not True:
        raise OperationalClosedLoopError(
            "embedded prepared result must be valid"
        )


def _policy_decision_id(value: object) -> str:
    normalized = str(value).strip()
    if not normalized.startswith("policy:"):
        raise OperationalClosedLoopError(
            "policy-decision-id must start with policy:"
        )
    return normalized


@contextmanager
def _runtime_config_scope(
    path: Path | None,
) -> Iterator[None]:
    if path is None:
        yield
        return

    resolved = _absolute_input(path)
    if not resolved.is_file():
        raise OperationalClosedLoopError(
            f"runtime config not found: {resolved}"
        )
    variable = "AUTODOC_LOVE_INSTALLED_RUNTIME_CONFIG"
    previous = os.environ.get(variable)
    os.environ[variable] = str(resolved)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(variable, None)
        else:
            os.environ[variable] = previous


def _load_callable(path: str) -> Callable[..., object]:
    normalized = path.strip()
    module_name, separator, attribute = normalized.partition(":")
    if not separator or not module_name or not attribute:
        raise OperationalClosedLoopError(
            "factory path must use module:function"
        )
    module = importlib.import_module(module_name)
    value = getattr(module, attribute, None)
    if not callable(value):
        raise OperationalClosedLoopError(
            f"factory is not callable: {normalized}"
        )
    return value


def _read_mapping(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise OperationalClosedLoopError(f"{label} not found: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OperationalClosedLoopError(
            f"{label} is not valid JSON: {path}"
        ) from exc
    if not isinstance(value, Mapping):
        raise OperationalClosedLoopError(
            f"{label} must contain a JSON object"
        )
    return dict(value)


def _required_mapping(
    value: Mapping[str, Any],
    name: str,
) -> Mapping[str, Any]:
    candidate = value.get(name)
    if not isinstance(candidate, Mapping):
        raise OperationalClosedLoopError(f"{name} must be an object")
    return candidate


def _required_text(
    value: Mapping[str, Any],
    name: str,
) -> str:
    candidate = value.get(name)
    if not isinstance(candidate, str) or not candidate.strip():
        raise OperationalClosedLoopError(f"{name} must not be empty")
    return candidate.strip()


def _utc_timestamp(value: str | None) -> str:
    if value is None or not value.strip():
        return (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
    normalized = value.strip()
    if "T" not in normalized or not normalized.endswith("Z"):
        raise OperationalClosedLoopError(
            "timestamp must be UTC and end with Z"
        )
    return normalized


def _absolute_input(path: Path) -> Path:
    return (
        path.resolve()
        if path.is_absolute()
        else (_REPO_ROOT / path).resolve()
    )


def _absolute_output(path: Path) -> Path:
    return path if path.is_absolute() else _REPO_ROOT / path


def _write_json_atomic(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _common_boundaries() -> dict[str, object]:
    return {
        "application_tool_only": True,
        "existing_scheduler_reused": True,
        "new_scheduler_created": False,
        "new_dispatcher_created": False,
        "new_eventbus_created": False,
        "new_sql_store_created": False,
        "new_qdrant_client_created": False,
        "new_openvino_runtime_created": False,
        "new_laboratory_provider_created": False,
        "existing_github_cli_adapter_reused": True,
        "project_target_resolution_read_only": True,
        "secret_value_serialized": False,
    }


def _emit(payload: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return
    print(
        " ".join(
            (
                f"valid={str(payload.get('valid')).lower()}",
                f"mode={payload.get('mode', '')}",
                f"status={payload.get('status', '')}",
                (
                    "plan_digest="
                    f"{payload.get('publication_plan_digest', '')}"
                ),
                (
                    "cycle_closed="
                    f"{str(payload.get('status') == 'closed').lower()}"
                ),
            )
        )
    )
    for issue in payload.get("issues", ()):
        print(f"issue: {issue}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
