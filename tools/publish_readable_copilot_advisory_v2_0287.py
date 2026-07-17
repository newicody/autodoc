#!/usr/bin/env python3
"""Preview or execute readable Copilot v2 publication on Issue and ProjectV2."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
_PROJECT_SCRIPTS = (
    _REPO_ROOT / "templates/github/projects-repository/scripts"
)
for path in (_SRC_ROOT, _PROJECT_SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from context.github_copilot_advisory_v2_issue_publication_0287 import (  # noqa: E402
    CopilotAdvisoryV2IssuePublicationCommand,
    plan_copilot_advisory_v2_issue_publication,
)
from context.readable_copilot_publication_wiring_0287 import (  # noqa: E402
    build_combined_publication_plan,
    enrich_projectv2_preview,
    plan_readable_issue_publication,
    resolve_readable_copilot_publication_identity,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--artifact-identity", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("projectv2_views.json"))
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--policy-decision-id", required=True)
    parser.add_argument("--operator-decision", choices=("approve",), required=True)
    parser.add_argument("--updated-date", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-plan-digest", default="")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(tuple(sys.argv[1:] if argv is None else argv))
    try:
        report, state = _build_preview(args)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        _emit({"valid": False, "issues": [str(exc)]}, args.format)
        return 2

    combined = report["combined_plan"]
    if not args.execute:
        Path(state["project_preview_path"]).unlink(missing_ok=True)
        _emit(report, args.format)
        return 0 if combined["valid"] else 2
    if not combined["valid"]:
        Path(state["project_preview_path"]).unlink(missing_ok=True)
        _emit(report, args.format)
        return 2
    gates = (
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "AUTODOC_ISSUE_PUBLICATION_ALLOWED",
        "AUTODOC_PROJECT_PROJECTION_ALLOWED",
    )
    missing = [name for name in gates if not _enabled(name)]
    if missing:
        Path(state["project_preview_path"]).unlink(missing_ok=True)
        report["execution_error"] = "locked gates: " + ", ".join(missing)
        _emit(report, args.format)
        return 3
    if args.confirm_plan_digest != combined["plan_digest"]:
        Path(state["project_preview_path"]).unlink(missing_ok=True)
        report["execution_error"] = "confirm-plan-digest mismatch"
        _emit(report, args.format)
        return 3

    try:
        issue_result = _execute_issue(state, args)
    except (RuntimeError, TypeError, ValueError) as exc:
        Path(state["project_preview_path"]).unlink(missing_ok=True)
        report["issue_execution"] = {
            "action": state["issue_plan"].action,
            "mutation_performed": False,
            "readback_verified": False,
            "error": str(exc),
        }
        report["execution_status"] = "issue_failed"
        _emit(report, args.format)
        return 4
    report["issue_execution"] = issue_result
    if not issue_result["readback_verified"]:
        Path(state["project_preview_path"]).unlink(missing_ok=True)
        report["execution_status"] = "issue_failed"
        _emit(report, args.format)
        return 4

    try:
        project_result = _execute_project(state, args)
    except (RuntimeError, TypeError, ValueError) as exc:
        report["project_execution"] = {
            "action": state["project_action"],
            "mutation_performed": False,
            "readback_verified": False,
            "error": str(exc),
        }
        report["execution_status"] = "partial"
        _emit(report, args.format)
        return 4
    report["project_execution"] = project_result
    report["execution_status"] = "completed"
    report["mutation_performed"] = bool(
        issue_result["mutation_performed"]
        or project_result["mutation_performed"]
    )
    report["readback_verified"] = bool(
        issue_result["readback_verified"]
        and project_result["readback_verified"]
    )
    _emit(report, args.format)
    return 0


def _build_preview(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    preview = _read_mapping(args.preview, "publication preview")
    identity_bundle = _read_mapping(args.artifact_identity, "artifact identity")
    identity = resolve_readable_copilot_publication_identity(
        preview, identity_bundle
    )
    if identity.repository != args.repository or identity.issue_number != args.issue_number:
        raise ValueError("CLI target does not match the readable artifact identity")

    issue_adapter = _load_module(
        _REPO_ROOT / "tools/publish_github_copilot_advisory_v2_issue_comment_0287.py",
        "autodoc_existing_copilot_issue_adapter_0287",
    )
    comments = issue_adapter._fetch_comments(  # type: ignore[attr-defined]
        args.gh_command, args.repository, args.issue_number
    )
    comment_mappings = tuple(
        {
            "id": item.comment_id,
            "body": item.body,
            "html_url": item.html_url,
        }
        for item in comments
    )
    base_plan = plan_copilot_advisory_v2_issue_publication(
        CopilotAdvisoryV2IssuePublicationCommand(
            repository=args.repository,
            issue_number=args.issue_number,
            policy_decision_id=args.policy_decision_id,
            operator_decision=args.operator_decision,
            publication_preview=preview,
            existing_comments=(),
        )
    )
    issue_plan = plan_readable_issue_publication(
        base_plan=base_plan.to_mapping(),
        identity=identity,
        existing_comments=comment_mappings,
        policy_decision_id=args.policy_decision_id,
    )

    project_module = _load_module(
        _PROJECT_SCRIPTS / "project_copilot_advisory_v2_fields.py",
        "autodoc_existing_copilot_projectv2_adapter_0287",
    )
    enriched_preview = enrich_projectv2_preview(preview, identity)
    temporary = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        prefix="autodoc-readable-copilot-",
        delete=False,
    )
    try:
        json.dump(enriched_preview, temporary, ensure_ascii=False, indent=2, sort_keys=True)
        temporary.write("\n")
        temporary.close()
        command = project_module.CopilotFieldProjectionCommand(
            configuration_path=args.config,
            preview_path=Path(temporary.name),
            repository=args.repository,
            issue_number=args.issue_number,
            policy_decision_id=args.policy_decision_id,
            operator_decision=args.operator_decision,
            updated_date=args.updated_date,
            execute=False,
            remote_mutation_allowed=False,
            project_projection_allowed=False,
            confirm_plan_digest="",
        )
        transport = project_module.GhGraphQLTransport(
            token=os.environ.get("AUTODOC_PROJECT_TOKEN", ""),
            command=args.gh_command,
        )
        project_plan = project_module.plan_copilot_v2_field_projection(
            command, transport=transport
        )
        project_action = _project_action(project_module, transport, project_plan)
    except Exception:
        Path(temporary.name).unlink(missing_ok=True)
        raise

    combined = build_combined_publication_plan(
        issue_plan=issue_plan,
        project_plan_digest=project_plan.plan_digest,
        project_action=project_action,
        identity=identity,
        policy_decision_id=args.policy_decision_id,
        project_valid=project_plan.valid,
        project_issues=project_plan.issues,
    )
    report = {
        "schema": "autodoc.readable_copilot_publication_adapter.v1",
        "mode": "execute" if args.execute else "preview",
        "readable_identity": identity.to_mapping(),
        "issue_plan": issue_plan.to_mapping(),
        "project_plan": {
            **project_plan.to_mapping(),
            "action": project_action,
        },
        "combined_plan": combined.to_mapping(),
        "mutation_performed": False,
        "readback_verified": (
            issue_plan.action == "replay" and project_action == "replay"
        ),
    }
    state = {
        "identity": identity,
        "issue_plan": issue_plan,
        "issue_adapter": issue_adapter,
        "project_module": project_module,
        "project_transport": transport,
        "project_plan": project_plan,
        "project_action": project_action,
        "project_command": command,
        "project_preview_path": Path(temporary.name),
    }
    return report, state


def _project_action(module: ModuleType, transport: Any, plan: Any) -> str:
    if not plan.valid:
        return "invalid"
    readback = transport.graphql(module._readback_query(), {"item": plan.item_id})
    try:
        module._verify_readback(
            readback,
            item_id=plan.item_id,
            mutations=plan.mutations,
        )
    except RuntimeError:
        return "update"
    return "replay"


def _execute_issue(state: Mapping[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    plan = state["issue_plan"]
    adapter = state["issue_adapter"]
    if plan.action == "replay":
        return {
            "action": "replay",
            "mutation_performed": False,
            "readback_verified": True,
            "comment_url": plan.existing_comment_url,
        }
    if plan.action != "create":
        return {
            "action": plan.action,
            "mutation_performed": False,
            "readback_verified": False,
            "comment_url": "",
        }
    published = adapter._gh_json(  # type: ignore[attr-defined]
        args.gh_command,
        (
            "api",
            "--method",
            "POST",
            f"repos/{args.repository}/issues/{args.issue_number}/comments",
            "-f",
            f"body={plan.body}",
        ),
    )
    comments = adapter._fetch_comments(  # type: ignore[attr-defined]
        args.gh_command, args.repository, args.issue_number
    )
    matches = tuple(item for item in comments if plan.marker in item.body)
    verified = len(matches) == 1 and matches[0].body == plan.body
    if not verified:
        raise RuntimeError("readable Copilot Issue comment readback mismatch")
    return {
        "action": "created",
        "mutation_performed": True,
        "readback_verified": True,
        "comment_url": str(published.get("html_url", ""))
        if isinstance(published, Mapping)
        else "",
    }


def _execute_project(state: Mapping[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    action = str(state["project_action"])
    path = Path(state["project_preview_path"])
    try:
        if action == "replay":
            return {
                "action": "replay",
                "mutation_performed": False,
                "readback_verified": True,
            }
        if action != "update":
            raise RuntimeError(f"unsupported ProjectV2 action: {action}")
        module = state["project_module"]
        base = state["project_command"]
        plan = state["project_plan"]
        command = module.CopilotFieldProjectionCommand(
            configuration_path=base.configuration_path,
            preview_path=base.preview_path,
            repository=base.repository,
            issue_number=base.issue_number,
            policy_decision_id=base.policy_decision_id,
            operator_decision=base.operator_decision,
            updated_date=base.updated_date,
            execute=True,
            remote_mutation_allowed=True,
            project_projection_allowed=True,
            confirm_plan_digest=plan.plan_digest,
        )
        result = module.execute_copilot_v2_field_projection(
            command, transport=state["project_transport"]
        )
        return {
            "action": "updated",
            "mutation_performed": result.mutation_performed,
            "readback_verified": result.readback_verified,
        }
    finally:
        path.unlink(missing_ok=True)


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _read_mapping(path: Path, name: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{name} file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return dict(payload)


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _emit(report: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return
    combined = report.get("combined_plan", report)
    print(f"valid: {str(bool(combined.get('valid'))).lower()}")
    if combined.get("plan_digest"):
        print(f"plan_digest: {combined['plan_digest']}")
    if combined.get("issue_action"):
        print(f"issue_action: {combined['issue_action']}")
    if combined.get("project_action"):
        print(f"project_action: {combined['project_action']}")
    identity = report.get("readable_identity")
    if isinstance(identity, Mapping):
        print(f"artifact: {identity.get('display_title', '')}")
        print(f"run_url: {identity.get('workflow_run_url', '')}")
    for issue in combined.get("issues", report.get("issues", ())):
        print(f"issue: {issue}")


if __name__ == "__main__":
    raise SystemExit(main())
