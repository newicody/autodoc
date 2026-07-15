#!/usr/bin/env python3
"""Download, validate and project one operator-approved Copilot advisory."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import date
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from build_copilot_advisory_publication_preview import (
    build_copilot_advisory_publication_preview,
)
from project_copilot_advisory_fields import (
    CopilotFieldProjectionCommand,
    GhGraphQLTransport,
    execute_copilot_field_projection,
)


_ARTIFACTS = {
    "request": (
        "autodoc-authoritative-request",
        "authoritative_request.json",
    ),
    "advisory": (
        "autodoc-copilot-advisory",
        "copilot_advisory.json",
    ),
    "manifest": (
        "autodoc-dual-artifact-manifest",
        "dual_artifact_manifest.json",
    ),
}
_REPORT_SCHEMA = (
    "autodoc.github.copilot_advisory_projectv2_publication_run.v1"
)


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _run_download(
    *,
    gh_command: str,
    repository: str,
    run_id: str,
    artifact_name: str,
    destination: Path,
    token: str,
) -> None:
    environment = dict(os.environ)
    environment["GH_TOKEN"] = token
    completed = subprocess.run(
        [
            gh_command,
            "run",
            "download",
            run_id,
            "--repo",
            repository,
            "--name",
            artifact_name,
            "--dir",
            str(destination),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "unknown gh failure"
        raise RuntimeError(
            f"cannot download {artifact_name}: {detail}"
        )


def _find_artifact(directory: Path, filename: str) -> Path:
    matches = tuple(directory.rglob(filename))
    if len(matches) != 1:
        raise ValueError(
            f"expected one {filename} under {directory}, got {len(matches)}"
        )
    return matches[0]


def _download_artifacts(
    *,
    repository: str,
    run_id: str,
    workdir: Path,
    gh_command: str,
    token: str,
) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for key, (artifact_name, filename) in _ARTIFACTS.items():
        destination = workdir / artifact_name
        destination.mkdir(parents=True, exist_ok=True)
        _run_download(
            gh_command=gh_command,
            repository=repository,
            run_id=run_id,
            artifact_name=artifact_name,
            destination=destination,
            token=token,
        )
        paths[key] = _find_artifact(destination, filename)
    return paths


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or execute an operator-approved Copilot advisory "
            "projection into ProjectV2 fields."
        )
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("projectv2_views.json"),
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path(".var/copilot-advisory-publication"),
    )
    parser.add_argument("--policy-decision-id", required=True)
    parser.add_argument(
        "--operator-decision",
        choices=("approve",),
        required=True,
    )
    parser.add_argument(
        "--updated-date",
        default=date.today().isoformat(),
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-plan-digest", default="")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
    )
    return parser


def _emit(report: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return
    projection = report["projection"]
    print(f"mode: {report['mode']}")
    print(f"preview_path: {report['preview_path']}")
    print(f"valid: {str(projection['valid']).lower()}")
    print(f"plan_digest: {projection['plan_digest']}")
    print(f"mutations: {len(projection['mutations'])}")
    print(
        "mutation_performed: "
        f"{str(projection['mutation_performed']).lower()}"
    )
    for issue in projection["issues"]:
        print(f"issue: {issue}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(
        tuple(sys.argv[1:] if argv is None else argv)
    )
    if not args.policy_decision_id.startswith("policy:"):
        raise ValueError("policy_decision_id must start with policy:")

    token = os.environ.get("AUTODOC_PROJECT_TOKEN", "").strip()
    if not token:
        raise ValueError("AUTODOC_PROJECT_TOKEN is required")

    run_workdir = args.workdir / str(args.run_id)
    artifact_paths = _download_artifacts(
        repository=args.repository,
        run_id=str(args.run_id),
        workdir=run_workdir,
        gh_command=args.gh_command,
        token=token,
    )
    preview_path = run_workdir / "publication_preview.json"
    preview = build_copilot_advisory_publication_preview(
        advisory_path=artifact_paths["advisory"],
        request_path=artifact_paths["request"],
        manifest_path=artifact_paths["manifest"],
        run_id=str(args.run_id),
        repository=args.repository,
        issue_number=args.issue_number,
    )
    preview_path.write_text(
        json.dumps(
            preview,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    command = CopilotFieldProjectionCommand(
        configuration_path=args.config,
        preview_path=preview_path,
        repository=args.repository,
        issue_number=args.issue_number,
        policy_decision_id=args.policy_decision_id,
        operator_decision=args.operator_decision,
        updated_date=args.updated_date,
        execute=args.execute,
        remote_mutation_allowed=_enabled(
            "AUTODOC_REMOTE_MUTATION_ALLOWED"
        ),
        project_projection_allowed=_enabled(
            "AUTODOC_PROJECT_PROJECTION_ALLOWED"
        ),
        confirm_plan_digest=args.confirm_plan_digest,
    )
    transport = GhGraphQLTransport(
        token=token,
        command=args.gh_command,
    )
    plan = execute_copilot_field_projection(
        command,
        transport=transport,
    )
    report = {
        "schema": _REPORT_SCHEMA,
        "mode": "execute" if args.execute else "preview",
        "repository": args.repository,
        "issue_number": args.issue_number,
        "run_id": str(args.run_id),
        "preview_path": str(preview_path),
        "artifacts": {
            key: str(path)
            for key, path in sorted(artifact_paths.items())
        },
        "operator_decision": args.operator_decision,
        "policy_decision_id": args.policy_decision_id,
        "projection": plan.to_mapping(),
        "workflow_self_authorized": False,
        "advisory_is_authority": False,
    }
    _emit(report, args.format)
    return 0 if plan.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
