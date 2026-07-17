#!/usr/bin/env python3
"""Project one locally fetched Copilot advisory v2 into ProjectV2 fields.

The command composes the existing v2 preview builder and v2 ProjectV2 field
adapter.  It never downloads artifacts again.  Preview is the default; execute
still requires both environment gates and the exact confirmed plan digest.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import date
import importlib
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.github_actions_ready_run_copilot_v2_projection_0287 import (  # noqa: E402
    resolve_local_ready_run_projection_input,
)

_REPORT_SCHEMA = (
    "missipy.github_actions.ready_run_copilot_v2_projectv2_projection_run.v1"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve one ready_run from the durable raw dataset and compose "
            "the existing Copilot advisory v2 ProjectV2 projection adapters."
        )
    )
    parser.add_argument(
        "--scan-report",
        type=Path,
        default=Path("/tmp/github-actions-artifact-ready-runs.json"),
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path(".var/server_datasets/github_artifacts"),
    )
    parser.add_argument(
        "--projects-scripts-dir",
        type=Path,
        default=ROOT / "templates/github/projects-repository/scripts",
    )
    parser.add_argument(
        "--project-config",
        type=Path,
        default=Path("/home/eric/projet/git/projects/projectv2_views.json"),
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path(".var/github/project_v2/copilot_advisory_v2_projection"),
    )
    parser.add_argument("--repository", default="newicody/projects")
    parser.add_argument("--policy-decision-id", required=True)
    parser.add_argument("--operator-decision", choices=("approve",), required=True)
    parser.add_argument("--updated-date", default=date.today().isoformat())
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-plan-digest", default="")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    return parser


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _load_existing_v2_adapters(scripts_dir: Path) -> tuple[Any, Any]:
    if not scripts_dir.is_dir():
        raise ValueError(f"Projects scripts directory not found: {scripts_dir}")
    required = (
        "build_copilot_advisory_v2_publication_preview.py",
        "project_copilot_advisory_fields.py",
        "project_copilot_advisory_v2_fields.py",
    )
    missing = [name for name in required if not (scripts_dir / name).is_file()]
    if missing:
        raise ValueError("missing existing Projects v2 adapter(s): " + ", ".join(missing))
    scripts_text = str(scripts_dir.resolve())
    if scripts_text not in sys.path:
        sys.path.insert(0, scripts_text)
    preview_module = importlib.import_module(
        "build_copilot_advisory_v2_publication_preview"
    )
    fields_module = importlib.import_module("project_copilot_advisory_v2_fields")
    return preview_module, fields_module


def _emit(report: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return
    projection = report["projection"]
    print(f"mode: {report['mode']}")
    print(f"run_id: {report['run_id']}")
    print(f"issue_number: {report['issue_number']}")
    print(f"preview_path: {report['preview_path']}")
    print(f"valid: {str(projection['valid']).lower()}")
    print(f"plan_digest: {projection['plan_digest']}")
    print(f"mutations: {len(projection['mutations'])}")
    print(f"mutation_performed: {str(projection['mutation_performed']).lower()}")
    print(f"readback_verified: {str(projection['readback_verified']).lower()}")
    for issue in projection["issues"]:
        print(f"issue: {issue}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(tuple(sys.argv[1:] if argv is None else argv))
    if not args.policy_decision_id.startswith("policy:"):
        raise ValueError("policy_decision_id must start with policy:")

    projection_input = resolve_local_ready_run_projection_input(
        scan_report_path=args.scan_report,
        run_id=str(args.run_id),
        dataset_root=args.dataset_root,
        expected_repository=args.repository,
    )
    preview_module, fields_module = _load_existing_v2_adapters(
        args.projects_scripts_dir
    )

    run_workdir = args.workdir / projection_input.run_id
    run_workdir.mkdir(parents=True, exist_ok=True)
    projection_input_path = run_workdir / "local_ready_run_projection_input.json"
    projection_input_path.write_text(
        json.dumps(
            projection_input.to_mapping(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    preview = preview_module.build_copilot_advisory_v2_publication_preview(
        advisory_path=projection_input.advisory.path,
        request_path=projection_input.request.path,
        manifest_path=projection_input.manifest.path,
        run_id=projection_input.run_id,
        repository=projection_input.repository,
        issue_number=projection_input.issue_number,
    )
    preview_path = run_workdir / "publication_preview_v2.json"
    preview_path.write_text(
        json.dumps(preview, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    token = os.environ.get("AUTODOC_PROJECT_TOKEN", "").strip()
    if not token:
        raise ValueError("AUTODOC_PROJECT_TOKEN is required for ProjectV2 inventory/readback")

    command = fields_module.CopilotFieldProjectionCommand(
        configuration_path=args.project_config,
        preview_path=preview_path,
        repository=projection_input.repository,
        issue_number=projection_input.issue_number,
        policy_decision_id=args.policy_decision_id,
        operator_decision=args.operator_decision,
        updated_date=args.updated_date,
        execute=args.execute,
        remote_mutation_allowed=_enabled("AUTODOC_REMOTE_MUTATION_ALLOWED"),
        project_projection_allowed=_enabled("AUTODOC_PROJECT_PROJECTION_ALLOWED"),
        confirm_plan_digest=args.confirm_plan_digest,
    )
    transport = fields_module.GhGraphQLTransport(
        token=token,
        command=args.gh_command,
    )
    plan = fields_module.execute_copilot_v2_field_projection(
        command,
        transport=transport,
    )

    report = {
        "schema": _REPORT_SCHEMA,
        "mode": "execute" if args.execute else "preview",
        "repository": projection_input.repository,
        "run_id": projection_input.run_id,
        "issue_number": projection_input.issue_number,
        "handoff_ref": projection_input.handoff_ref,
        "policy_decision_id": args.policy_decision_id,
        "operator_decision": args.operator_decision,
        "projection_input_path": str(projection_input_path),
        "preview_path": str(preview_path),
        "projection": plan.to_mapping(),
        "boundaries": {
            "durable_raw_dataset_only": True,
            "github_artifact_download_performed": False,
            "existing_v2_preview_builder_reused": True,
            "existing_v2_projectv2_adapter_reused": True,
            "operator_decision_required": True,
            "confirmed_plan_digest_required_for_execute": True,
            "remote_mutation_allowed": _enabled("AUTODOC_REMOTE_MUTATION_ALLOWED"),
            "project_projection_allowed": _enabled(
                "AUTODOC_PROJECT_PROJECTION_ALLOWED"
            ),
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "laboratory_execution_started": False,
            "scheduler_modified": False,
        },
    }
    _emit(report, args.format)
    return 0 if plan.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
