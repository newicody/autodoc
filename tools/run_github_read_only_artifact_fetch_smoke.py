#!/usr/bin/env python3
"""GitHub read-only artifact fetch/import smoke.

0164 is a local-only dry run for the next GitHub phase. It uses existing
SourceCandidate/GitHub boundary builders instead of creating a new adapter:

- SourceCandidateReadOnlyExternalProbeRequest
- FakeSourceCandidateReadOnlyExternalProbeAdapter
- SourceCandidateExternalProbeBundle
- SourceCandidateExternalProjectionContract
- SourceCandidateGithubProjectionPayload
- run_source_candidate_remote_mutation_gate

The smoke performs no GitHub API call, no external network, no SQL write, no
qdrant write, no Scheduler execution, no LLM execution and no openvino
execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))


from context.source_candidate_external_probe_bundle import (  # noqa: E402
    build_source_candidate_external_probe_bundle,
    render_source_candidate_external_probe_bundle,
)
from context.source_candidate_external_projection_contract import (  # noqa: E402
    SourceCandidateExternalProjectionContractPolicy,
    build_source_candidate_external_projection_contract,
    write_source_candidate_external_projection_contract,
)
from context.source_candidate_github_projection_payload import (  # noqa: E402
    SourceCandidateGithubProjectionPayloadPolicy,
    build_source_candidate_github_projection_payload,
    write_source_candidate_github_projection_payload,
)
from context.source_candidate_read_only_external_probe import (  # noqa: E402
    FakeSourceCandidateReadOnlyExternalProbeAdapter,
    build_source_candidate_read_only_external_probe_request_from_file,
    render_source_candidate_read_only_external_probe_result,
    write_source_candidate_read_only_external_probe_request,
    write_source_candidate_read_only_external_probe_result,
)
from context.source_candidate_remote_mutation_gate import (  # noqa: E402
    SourceCandidateRemoteMutationGatePolicy,
    render_source_candidate_remote_mutation_gate,
    run_source_candidate_remote_mutation_gate,
    write_source_candidate_remote_mutation_gate_result,
)


DEFAULT_OUTPUT_DIR = ".var/smoke/artifacts/0164"
DEFAULT_DEVELOPMENT_REPOSITORY = "newicody/autodoc"
DEFAULT_EXTERNAL_REPOSITORY = "newicody/autodoc-ideas"
DEFAULT_PROJECT_KEY = "autodoc-ideas"
_OPERATOR_REVIEW_SCHEMA = "missipy.source_candidate.operator_external_review_report.v1"

_EXISTING_BUILDERS_USED = (
    "SourceCandidateReadOnlyExternalProbeRequest",
    "FakeSourceCandidateReadOnlyExternalProbeAdapter",
    "build_source_candidate_read_only_external_probe_request_from_file",
    "write_source_candidate_read_only_external_probe_request",
    "write_source_candidate_read_only_external_probe_result",
    "build_source_candidate_external_probe_bundle",
    "SourceCandidateExternalProjectionContractPolicy",
    "build_source_candidate_external_projection_contract",
    "write_source_candidate_external_projection_contract",
    "SourceCandidateGithubProjectionPayloadPolicy",
    "build_source_candidate_github_projection_payload",
    "write_source_candidate_github_projection_payload",
    "SourceCandidateRemoteMutationGatePolicy",
    "run_source_candidate_remote_mutation_gate",
    "write_source_candidate_remote_mutation_gate_result",
)

_PERFORMED_ACTIONS_FALSE = {
    "github_api_call": False,
    "external_network": False,
    "github_mutation": False,
    "sql_write": False,
    "qdrant_write": False,
    "scheduler_execution": False,
    "llm_execution": False,
    "openvino_execution": False,
}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local-only GitHub read-only artifact fetch/import smoke.")
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--development-repository", default=DEFAULT_DEVELOPMENT_REPOSITORY)
    parser.add_argument("--external-repository", default=DEFAULT_EXTERNAL_REPOSITORY)
    parser.add_argument("--project-key", default=DEFAULT_PROJECT_KEY)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    root = args.repository_root.resolve()
    output_dir = _resolve_repo_path(root, args.output_dir)

    plan = build_github_read_only_artifact_fetch_plan(
        repository_root=root,
        output_dir=output_dir,
        development_repository=args.development_repository,
        external_repository=args.external_repository,
        project_key=args.project_key,
        execute=args.execute,
    )

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(render_plan_markdown(plan), end="")

    if not args.execute:
        return 0 if plan["ready"] else 2

    result = execute_github_read_only_artifact_fetch_smoke(
        repository_root=root,
        output_dir=output_dir,
        development_repository=args.development_repository,
        external_repository=args.external_repository,
        project_key=args.project_key,
    )

    print("==> github_read_only_artifact_fetch_smoke")
    print(render_result_markdown(result), end="")
    return 0 if result["status"] == "ok" else 1


def build_github_read_only_artifact_fetch_plan(
    *,
    repository_root: Path,
    output_dir: Path,
    development_repository: str,
    external_repository: str,
    project_key: str,
    execute: bool,
) -> dict[str, Any]:
    surfaces = {
        "read_only_external_probe": repository_root / "src" / "context" / "source_candidate_read_only_external_probe.py",
        "external_probe_bundle": repository_root / "src" / "context" / "source_candidate_external_probe_bundle.py",
        "external_projection_contract": repository_root / "src" / "context" / "source_candidate_external_projection_contract.py",
        "github_projection_payload": repository_root / "src" / "context" / "source_candidate_github_projection_payload.py",
        "remote_mutation_gate": repository_root / "src" / "context" / "source_candidate_remote_mutation_gate.py",
    }
    surface_rows = [
        {
            "key": key,
            "path": _display_path(path, repository_root),
            "status": "present" if path.exists() else "missing",
            "required": True,
        }
        for key, path in surfaces.items()
    ]
    return {
        "schema": "missipy.github_project.read_only_artifact_fetch_plan.v1",
        "repository_root": str(repository_root),
        "output_dir": str(output_dir),
        "development_repository": development_repository,
        "external_repository": external_repository,
        "project_key": project_key,
        "execute": execute,
        "ready": all(row["status"] == "present" for row in surface_rows)
        and validate_repository_boundary(
            development_repository=development_repository,
            external_repository=external_repository,
        )["allowed"],
        "surfaces": surface_rows,
        "existing_builders_used": list(_EXISTING_BUILDERS_USED),
        "boundary": [
            "external repository must be explicit",
            "external repository must not equal development repository",
            "read-only probe uses existing fake adapter",
            "remote mutation gate remains closed",
            "local artifacts only",
        ],
    }


def execute_github_read_only_artifact_fetch_smoke(
    *,
    repository_root: Path,
    output_dir: Path,
    development_repository: str,
    external_repository: str,
    project_key: str,
) -> dict[str, Any]:
    boundary = validate_repository_boundary(
        development_repository=development_repository,
        external_repository=external_repository,
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    operator_report_path = output_dir / "operator_external_review_report.json"
    probe_request_path = output_dir / "read_only_external_probe_request.json"
    probe_result_path = output_dir / "read_only_external_probe_result.json"
    probe_bundle_dir = output_dir / "external_probe_bundle"
    handoff_dir = output_dir / "projection_handoff"
    contract_path = output_dir / "external_projection_contract.json"
    github_payload_path = output_dir / "github_projection_payload.json"
    mutation_gate_path = output_dir / "remote_mutation_gate_result.json"
    result_json_path = output_dir / "github_read_only_artifact_fetch_smoke_result.json"
    result_md_path = output_dir / "github_read_only_artifact_fetch_smoke_report.md"

    operator_report = build_operator_external_review_report(
        repository=external_repository,
        project_key=project_key,
        allowed=boundary["allowed"],
    )
    _write_json(operator_report_path, operator_report)

    probe_request = build_source_candidate_read_only_external_probe_request_from_file(operator_report_path)
    write_source_candidate_read_only_external_probe_request(probe_request_path, probe_request)

    probe_result = FakeSourceCandidateReadOnlyExternalProbeAdapter(
        available_repositories=(external_repository,),
    ).probe(probe_request)
    write_source_candidate_read_only_external_probe_result(probe_result_path, probe_result)

    probe_bundle = build_source_candidate_external_probe_bundle(
        output_dir=probe_bundle_dir,
        operator_review_report_path=operator_report_path,
        probe_request_path=probe_request_path,
        probe_result_path=probe_result_path,
    )

    write_projection_handoff_fixture(
        handoff_dir=handoff_dir,
        repository=external_repository,
        project_key=project_key,
        probe_allowed=probe_result.probe_allowed,
    )

    contract = build_source_candidate_external_projection_contract(
        handoff_dir,
        SourceCandidateExternalProjectionContractPolicy(
            target_kind="github_project_surface",
            require_gate_pass=True,
            max_items=4,
        ),
    )
    write_source_candidate_external_projection_contract(contract_path, contract)

    github_payload = build_source_candidate_github_projection_payload(
        contract.to_json_dict(),
        SourceCandidateGithubProjectionPayloadPolicy(
            repository=external_repository,
            project_key=project_key,
            max_operations=4,
        ),
    )
    write_source_candidate_github_projection_payload(github_payload_path, github_payload)

    mutation_gate = run_source_candidate_remote_mutation_gate(
        github_payload.to_json_dict(),
        SourceCandidateRemoteMutationGatePolicy(
            remote_mutation_enabled=False,
            operator_confirmed=False,
            allowed_repositories=(external_repository,),
            require_projection_allowed=True,
            require_dry_run_payload=True,
            require_no_payload_remote_mutation=True,
            require_operations=False,
        ),
    )
    write_source_candidate_remote_mutation_gate_result(mutation_gate_path, mutation_gate)

    status = "ok" if (
        boundary["allowed"]
        and probe_result.read_only
        and probe_result.probe_allowed
        and not probe_result.external_call_performed
        and github_payload.dry_run
        and not github_payload.remote_mutation
        and not mutation_gate.mutation_allowed
    ) else "blocked"

    result = {
        "schema": "missipy.github_project.read_only_artifact_fetch_smoke_result.v1",
        "status": status,
        "development_repository": development_repository,
        "external_repository": external_repository,
        "project_key": project_key,
        "repository_boundary": boundary,
        "read_only": probe_result.read_only,
        "probe_allowed": probe_result.probe_allowed,
        "probe_finding_count": probe_result.finding_count,
        "external_call_performed": probe_result.external_call_performed,
        "bundle_manifest": str(probe_bundle.manifest_path),
        "contract_path": str(contract_path),
        "contract_projection_allowed": contract.projection_allowed,
        "github_payload_path": str(github_payload_path),
        "github_payload_dry_run": github_payload.dry_run,
        "github_payload_remote_mutation": github_payload.remote_mutation,
        "github_operation_count": github_payload.operation_count,
        "mutation_gate_path": str(mutation_gate_path),
        "mutation_allowed": mutation_gate.mutation_allowed,
        "mutation_gate_issue_count": mutation_gate.issue_count,
        "performed_actions": dict(_PERFORMED_ACTIONS_FALSE),
        "existing_builders_used": list(_EXISTING_BUILDERS_USED),
        "operator_report_path": str(operator_report_path),
        "probe_request_path": str(probe_request_path),
        "probe_result_path": str(probe_result_path),
        "result_json": str(result_json_path),
        "result_md": str(result_md_path),
        "probe_report": render_source_candidate_read_only_external_probe_result(probe_result),
        "bundle_report": render_source_candidate_external_probe_bundle(probe_bundle),
        "mutation_gate_report": render_source_candidate_remote_mutation_gate(mutation_gate),
    }

    _write_json(result_json_path, result)
    result_md_path.write_text(render_result_markdown(result), encoding="utf-8")
    return result


def validate_repository_boundary(*, development_repository: str, external_repository: str) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not _is_owner_name(development_repository):
        issues.append({"code": "development_repository_format", "message": "development repository must use owner/name"})
    if not _is_owner_name(external_repository):
        issues.append({"code": "external_repository_format", "message": "external repository must use owner/name"})
    if external_repository == development_repository:
        issues.append({"code": "development_repo_ingestion", "message": "external artifact source must not be the development repository"})
    return {
        "allowed": not issues,
        "issues": issues,
        "development_repository": development_repository,
        "external_repository": external_repository,
    }


def build_operator_external_review_report(*, repository: str, project_key: str, allowed: bool) -> dict[str, Any]:
    return {
        "schema": _OPERATOR_REVIEW_SCHEMA,
        "repository": repository,
        "project_key": project_key,
        "dry_run": True,
        "recommended_action": "operator_review" if allowed else "review_gate_blockers",
        "target_kind": "github_project_surface",
        "notes": [
            "Local read-only probe request for an external GitHub Project surface.",
            "No GitHub API call is performed by this smoke.",
        ],
    }


def write_projection_handoff_fixture(
    *,
    handoff_dir: Path,
    repository: str,
    project_key: str,
    probe_allowed: bool,
) -> None:
    handoff_dir.mkdir(parents=True, exist_ok=True)
    candidate_id = f"github-read-only:{_digest(repository + ':' + project_key)}"
    _write_json(
        handoff_dir / "handoff_manifest.json",
        {
            "schema": "missipy.source_candidate.projection_handoff_manifest.v1",
            "passed": bool(probe_allowed),
            "repository": repository,
            "project_key": project_key,
        },
    )
    _write_json(
        handoff_dir / "projection_preview.json",
        {
            "schema": "missipy.source_candidate.projection_preview.v1",
            "items": [
                {
                    "candidate_id": candidate_id,
                    "title": "Read-only GitHub artifact fetch smoke",
                    "status": "current",
                    "recommended_action": "review",
                    "audit_present": True,
                    "labels": ["status:current", "decision:review"],
                    "decision_action": "operator_review",
                    "target_context_id": "github:project-item:read-only-fetch-0164",
                }
            ],
        },
    )
    _write_json(
        handoff_dir / "projection_gate_report.json",
        {
            "schema": "missipy.source_candidate.projection_gate_report.v1",
            "gate_result": {
                "passed": bool(probe_allowed),
                "repository": repository,
                "project_key": project_key,
            },
        },
    )


def render_plan_markdown(plan: Mapping[str, Any]) -> str:
    lines = [
        "# GitHub read-only artifact fetch/import smoke plan",
        "",
        f"ready: `{plan.get('ready')}`",
        f"development_repository: `{plan.get('development_repository')}`",
        f"external_repository: `{plan.get('external_repository')}`",
        f"project_key: `{plan.get('project_key')}`",
        "",
        "## Existing surfaces",
        "",
        "| key | status | path |",
        "| --- | --- | --- |",
    ]
    for surface in plan.get("surfaces", []):
        lines.append(f"| {surface['key']} | {surface['status']} | `{surface['path']}` |")
    lines.extend([
        "",
        "## Boundary",
        "",
        "- existing builders only",
        "- fake read-only adapter only",
        "- remote mutation gate remains closed",
        "- no SQL write, no qdrant write, no GitHub API call, no external network",
        "",
    ])
    return "\n".join(lines)


def render_result_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        "# GitHub read-only artifact fetch/import smoke result",
        "",
        f"status: `{result.get('status')}`",
        f"development_repository: `{result.get('development_repository')}`",
        f"external_repository: `{result.get('external_repository')}`",
        f"read_only: `{result.get('read_only')}`",
        f"probe_allowed: `{result.get('probe_allowed')}`",
        f"external_call_performed: `{result.get('external_call_performed')}`",
        f"github_payload_dry_run: `{result.get('github_payload_dry_run')}`",
        f"github_payload_remote_mutation: `{result.get('github_payload_remote_mutation')}`",
        f"mutation_allowed: `{result.get('mutation_allowed')}`",
        "",
        "## Generated local artifacts",
        "",
        f"- operator_report_path: `{result.get('operator_report_path')}`",
        f"- probe_request_path: `{result.get('probe_request_path')}`",
        f"- probe_result_path: `{result.get('probe_result_path')}`",
        f"- bundle_manifest: `{result.get('bundle_manifest')}`",
        f"- contract_path: `{result.get('contract_path')}`",
        f"- github_payload_path: `{result.get('github_payload_path')}`",
        f"- mutation_gate_path: `{result.get('mutation_gate_path')}`",
        "",
        "## Remote mutation gate",
        "",
        "The gate is expected to remain closed in 0164.",
        "",
        result.get("mutation_gate_report", ""),
        "",
    ]
    return "\n".join(lines)


def _resolve_repo_path(root: Path, path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_absolute():
        return expanded
    return root / expanded


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _is_owner_name(repository: str) -> bool:
    if repository.count("/") != 1:
        return False
    owner, name = repository.split("/", 1)
    return bool(owner.strip()) and bool(name.strip())


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
