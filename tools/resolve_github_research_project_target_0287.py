#!/usr/bin/env python3
"""Resolve one Issue item and one field in an existing ProjectV2.

The tool reuses the read-only GraphQL resolver and GitHub CLI adapter already
used by controlled final-deliverable publication. It performs no mutation and
returns the exact ``project_item_id`` and ``field_ref`` required by the
r16-r20 operational runner.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from context.love_actions_closed_loop_resolution_0287 import (  # noqa: E402
    LoveProjectV2TargetRequest,
)
from tools.publish_love_final_deliverable_0287 import (  # noqa: E402
    GitHubCliFinalDeliverablePublicationAdapter,
)

SCHEMA = "missipy.github.research_projectv2_target_resolution.v1"


class GitHubResearchProjectTargetResolutionError(RuntimeError):
    """Raised when CLI inputs cannot produce one exact target."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--project-owner", required=True)
    parser.add_argument("--project-number", type=int, required=True)
    parser.add_argument("--field-name", default="Résumé")
    parser.add_argument("--project-item-id-override", default="")
    parser.add_argument("--field-ref-override", default="")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument("--token-env", default="AUTODOC_PROJECT_TOKEN")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--format",
        choices=("json", "summary", "shell"),
        default="summary",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(
        tuple(sys.argv[1:] if argv is None else argv)
    )
    try:
        payload = resolve_project_target_report(
            repository=str(args.repository),
            issue_number=int(args.issue_number),
            project_owner=str(args.project_owner),
            project_number=int(args.project_number),
            field_name=str(args.field_name),
            project_item_id_override=str(
                args.project_item_id_override
            ),
            field_ref_override=str(args.field_ref_override),
            gh_command=str(args.gh_command),
            token_env=str(args.token_env),
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        payload = {
            "schema": SCHEMA,
            "valid": False,
            "status": "failed",
            "issues": [f"{type(exc).__name__}: {exc}"],
            "target": None,
            "boundaries": _boundaries(),
        }

    if args.output is not None:
        _write_json_atomic(_absolute_output(args.output), payload)
    _emit(payload, str(args.format))
    return 0 if payload.get("valid") is True else 2


def resolve_project_target_report(
    *,
    repository: str,
    issue_number: int,
    project_owner: str,
    project_number: int,
    field_name: str,
    project_item_id_override: str = "",
    field_ref_override: str = "",
    gh_command: str = "gh",
    token_env: str = "AUTODOC_PROJECT_TOKEN",
    adapter_factory: type[
        GitHubCliFinalDeliverablePublicationAdapter
    ] = GitHubCliFinalDeliverablePublicationAdapter,
) -> dict[str, Any]:
    request = LoveProjectV2TargetRequest(
        repository=repository.strip(),
        issue_number=issue_number,
        project_owner=project_owner.strip(),
        project_number=project_number,
        field_name=field_name.strip(),
        project_item_id_override=project_item_id_override.strip(),
        field_ref_override=field_ref_override.strip(),
    )
    adapter = adapter_factory(
        gh_command=gh_command,
        token_env=token_env,
    )
    target = adapter.resolve_project_target(request)
    mapping = target.to_mapping()

    if mapping["project_owner"] != request.project_owner:
        raise GitHubResearchProjectTargetResolutionError(
            "resolved project owner mismatch"
        )
    if mapping["project_number"] != request.project_number:
        raise GitHubResearchProjectTargetResolutionError(
            "resolved project number mismatch"
        )
    if mapping["field_name"] != request.field_name:
        raise GitHubResearchProjectTargetResolutionError(
            "resolved field name mismatch"
        )

    return {
        "schema": SCHEMA,
        "valid": True,
        "status": "resolved",
        "issues": [],
        "request": {
            "repository": request.repository,
            "issue_number": request.issue_number,
            "project_owner": request.project_owner,
            "project_number": request.project_number,
            "field_name": request.field_name,
            "project_item_id_override": (
                request.project_item_id_override
            ),
            "field_ref_override": request.field_ref_override,
        },
        "target": mapping,
        "project_item_id": mapping["project_item_id"],
        "project_field_ref": mapping["field_ref"],
        "project_field_name": mapping["field_name"],
        "boundaries": _boundaries(),
    }


def _boundaries() -> dict[str, object]:
    return {
        "read_only_graphql_resolution": True,
        "existing_resolution_contract_reused": True,
        "existing_github_cli_adapter_reused": True,
        "remote_mutation_performed": False,
        "issue_comment_created": False,
        "project_field_updated": False,
        "scheduler_dispatch_started": False,
        "sql_write_performed": False,
        "qdrant_write_performed": False,
        "laboratory_execution_started": False,
        "token_value_serialized": False,
    }


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


def _shell_quote(value: object) -> str:
    text = str(value)
    return "'" + text.replace("'", "'\"'\"'") + "'"


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

    if output_format == "shell":
        if payload.get("valid") is not True:
            for issue in payload.get("issues", ()):
                print(f"# issue: {issue}")
            return
        print(
            "PROJECT_ITEM_ID="
            + _shell_quote(payload.get("project_item_id", ""))
        )
        print(
            "RESUME_FIELD_ID="
            + _shell_quote(payload.get("project_field_ref", ""))
        )
        print(
            "PROJECT_FIELD_NAME="
            + _shell_quote(payload.get("project_field_name", ""))
        )
        return

    print(
        " ".join(
            (
                f"valid={str(payload.get('valid')).lower()}",
                f"status={payload.get('status', '')}",
                (
                    "project_item_id="
                    f"{payload.get('project_item_id', '')}"
                ),
                (
                    "project_field_ref="
                    f"{payload.get('project_field_ref', '')}"
                ),
                (
                    "project_field_name="
                    f"{payload.get('project_field_name', '')}"
                ),
            )
        )
    )
    for issue in payload.get("issues", ()):
        print(f"issue: {issue}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
