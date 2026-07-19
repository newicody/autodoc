#!/usr/bin/env python3
"""Prepare one real GitHub research/love cycle up to operator confirmation.

This operator entrypoint composes existing one-shot application surfaces:

1. validate and optionally write the dedicated Actions scan configuration;
2. inspect installed PostgreSQL/Qdrant/OpenVINO readiness without writes;
3. run the canonical read-only GitHub Actions artifact fetch;
4. invoke the existing r16-r20 ``prepare`` command;
5. stop at the exact publication plan digest.

It never publishes to an Issue or ProjectV2 and never constructs a second
Scheduler, Dispatcher, SQL authority, Qdrant client, OpenVINO runtime or
laboratory provider.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from contextlib import redirect_stdout
import io
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

from tools import build_github_actions_artifact_scan_config_0287 as scan_builder  # noqa: E402
from tools import check_love_installed_runtime_0287 as runtime_check  # noqa: E402
from tools import run_github_actions_artifact_fetch_once_0287 as fetch_tool  # noqa: E402
from tools import run_github_research_love_closed_loop_0287 as closed_loop_tool  # noqa: E402

SCHEMA = "missipy.github.research_love_prepare_once.v1"
_DEFAULT_SCAN_CONFIG = Path(
    ".var/config/github_actions_artifact_scan.ini"
)
_DEFAULT_RUNTIME_FACTORY = (
    "context.love_installed_runtime_factory_0287:build_runtime"
)
_QDRANT_WRITE_GATE = "AUTODOC_QDRANT_POINT_WRITE_ALLOWED"
_QDRANT_SEARCH_GATE = "AUTODOC_QDRANT_SEARCH_ALLOWED"


class GitHubResearchLovePrepareOnceError(RuntimeError):
    """Raised when the one-command preparation must fail closed."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-config", type=Path, required=True)
    parser.add_argument("--fetch-config", type=Path, required=True)
    parser.add_argument(
        "--scan-config",
        type=Path,
        default=_DEFAULT_SCAN_CONFIG,
    )
    parser.add_argument("--runtime-config", type=Path, required=True)
    parser.add_argument(
        "--runtime-factory",
        default=_DEFAULT_RUNTIME_FACTORY,
    )
    parser.add_argument("--policy-decision-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--project-owner", required=True)
    parser.add_argument("--project-number", type=int, required=True)
    parser.add_argument("--project-field-name", default="Résumé")
    parser.add_argument(
        "--project-status-value",
        default="Livrable final prêt",
    )
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument(
        "--project-token-env",
        default="AUTODOC_PROJECT_TOKEN",
    )
    parser.add_argument("--max-runs", type=int, default=50)
    parser.add_argument("--max-artifacts", type=int, default=150)
    parser.add_argument(
        "--max-artifact-bytes",
        type=int,
        default=5 * 1024 * 1024,
    )
    parser.add_argument(
        "--working-directory",
        type=Path,
        default=_REPO_ROOT,
    )
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
    )
    parser.add_argument("--skip-openvino-compile", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--prepared-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
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
        payload = prepare_once_report(args)
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        payload = {
            "schema": SCHEMA,
            "valid": False,
            "mode": "execute" if args.execute else "plan",
            "status": "failed",
            "issues": [f"{type(exc).__name__}: {exc}"],
            "boundaries": _boundaries(
                execute=bool(args.execute),
                fetch_performed=False,
                prepare_performed=False,
            ),
        }

    _write_json_atomic(_absolute_output(args.output), payload)
    _emit(payload, str(args.format))
    return 0 if payload.get("valid") is True else 2


def prepare_once_report(
    args: argparse.Namespace,
) -> dict[str, Any]:
    policy_decision_id = _policy_decision_id(
        args.policy_decision_id
    )
    project_config = _absolute_input(args.project_config)
    fetch_config = _absolute_input(args.fetch_config)
    scan_config = _absolute_output(args.scan_config)
    runtime_config = _absolute_input(args.runtime_config)
    prepared_output = _absolute_output(args.prepared_output)

    scan = scan_builder.build_artifact_scan_config_report(
        project_config=project_config,
        fetch_config=fetch_config,
        output=scan_config,
        working_directory=_absolute_input(args.working_directory),
        python_executable=str(args.python_executable),
        execute=bool(args.execute),
    )
    if scan.get("valid") is not True:
        return _blocked(
            mode="execute" if args.execute else "plan",
            status="scan-config-blocked",
            issues=_issues(scan),
            scan=scan,
            runtime=None,
            fetch=None,
        )

    runtime = _runtime_readiness(
        runtime_config,
        compile_openvino_model=not bool(
            args.skip_openvino_compile
        ),
    )
    if runtime.get("valid") is not True:
        return _blocked(
            mode="execute" if args.execute else "plan",
            status="runtime-not-ready",
            issues=_issues(runtime),
            scan=scan,
            runtime=runtime,
            fetch=None,
        )

    if not args.execute:
        return {
            "schema": SCHEMA,
            "valid": True,
            "mode": "plan",
            "status": "ready-for-execute",
            "issues": [],
            "scan_configuration": scan,
            "runtime_readiness": runtime,
            "fetch_cycle": None,
            "prepared_cycle": None,
            "publication_plan_digest": "",
            "prepared_output": str(prepared_output),
            "next_command": (
                "rerun this command with --execute"
            ),
            "boundaries": _boundaries(
                execute=False,
                fetch_performed=False,
                prepare_performed=False,
            ),
        }

    _require_effect_gate(_QDRANT_WRITE_GATE)
    _require_effect_gate(_QDRANT_SEARCH_GATE)
    token_env = _required_text(scan, "token_env")
    if not os.environ.get(token_env, "").strip():
        raise GitHubResearchLovePrepareOnceError(
            f"missing GitHub artifact token environment {token_env}"
        )
    if not os.environ.get(
        str(args.project_token_env),
        "",
    ).strip():
        raise GitHubResearchLovePrepareOnceError(
            "missing ProjectV2 token environment "
            f"{args.project_token_env}"
        )

    fetch = _invoke_json_main(
        fetch_tool.main,
        (
            "--project-config",
            str(scan_config),
            "--fetch-config",
            str(fetch_config),
            "--policy-decision-id",
            policy_decision_id + ":fetch",
            "--max-runs",
            str(int(args.max_runs)),
            "--max-artifacts",
            str(int(args.max_artifacts)),
            "--execute",
            "--format",
            "json",
        ),
        label="artifact fetch",
    )
    if fetch.get("valid") is not True:
        return _blocked(
            mode="execute",
            status="artifact-fetch-failed",
            issues=_issues(fetch),
            scan=scan,
            runtime=runtime,
            fetch=fetch,
        )
    if fetch.get("status") != "artifacts-fetched":
        return _blocked(
            mode="execute",
            status="artifact-fetch-incomplete",
            issues=[
                "artifact fetch status must be artifacts-fetched"
            ],
            scan=scan,
            runtime=runtime,
            fetch=fetch,
        )

    reports = _required_mapping(fetch, "reports")
    fetch_cycle_report = _required_text(reports, "cycle")

    prepared = _invoke_json_main(
        closed_loop_tool.main,
        (
            "prepare",
            "--fetch-cycle-report",
            fetch_cycle_report,
            "--run-id",
            str(args.run_id),
            "--runtime-factory",
            str(args.runtime_factory),
            "--runtime-config",
            str(runtime_config),
            "--policy-decision-id",
            policy_decision_id + ":prepare",
            "--max-artifact-bytes",
            str(int(args.max_artifact_bytes)),
            "--issue-number",
            str(int(args.issue_number)),
            "--project-owner",
            str(args.project_owner),
            "--project-number",
            str(int(args.project_number)),
            "--project-field-name",
            str(args.project_field_name),
            "--project-status-value",
            str(args.project_status_value),
            "--gh-command",
            str(args.gh_command),
            "--token-env",
            str(args.project_token_env),
            "--output",
            str(prepared_output),
            "--format",
            "json",
        ),
        label="closed-loop prepare",
    )
    if prepared.get("valid") is not True:
        return _blocked(
            mode="execute",
            status="prepare-failed",
            issues=_issues(prepared),
            scan=scan,
            runtime=runtime,
            fetch=fetch,
            prepared=prepared,
        )

    digest = _required_text(
        prepared,
        "publication_plan_digest",
    )
    if prepared.get("status") != (
        "publication-confirmation-required"
    ):
        raise GitHubResearchLovePrepareOnceError(
            "prepared cycle did not stop at publication confirmation"
        )

    return {
        "schema": SCHEMA,
        "valid": True,
        "mode": "execute",
        "status": "publication-confirmation-required",
        "issues": [],
        "scan_configuration": scan,
        "runtime_readiness": runtime,
        "fetch_cycle": fetch,
        "fetch_cycle_report": fetch_cycle_report,
        "prepared_cycle": prepared,
        "prepared_output": str(prepared_output),
        "publication_plan_digest": digest,
        "next_command": (
            "python tools/run_github_research_love_closed_loop_0287.py "
            "complete --prepared-report "
            f"{prepared_output} --confirm-plan-digest {digest} "
            "--runtime-factory "
            f"{args.runtime_factory} --runtime-config {runtime_config} "
            "--output /tmp/github-love-completed.json"
        ),
        "boundaries": _boundaries(
            execute=True,
            fetch_performed=True,
            prepare_performed=True,
        ),
    }


def _runtime_readiness(
    config_path: Path,
    *,
    compile_openvino_model: bool,
) -> dict[str, Any]:
    settings = runtime_check.load_manual_installed_runtime_settings(
        str(config_path)
    )
    report = runtime_check.inspect_manual_runtime_readiness(
        settings,
        compile_openvino_model=compile_openvino_model,
    )
    mapping = dict(report.to_mapping())
    mapping["valid"] = bool(report.valid)
    return mapping


def _invoke_json_main(
    function: Callable[[Sequence[str] | None], int],
    argv: Sequence[str],
    *,
    label: str,
) -> dict[str, Any]:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        return_code = function(tuple(argv))
    raw = buffer.getvalue().strip()
    if not raw:
        raise GitHubResearchLovePrepareOnceError(
            f"{label} produced no JSON stdout"
        )
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GitHubResearchLovePrepareOnceError(
            f"{label} stdout is not valid JSON"
        ) from exc
    if not isinstance(value, Mapping):
        raise GitHubResearchLovePrepareOnceError(
            f"{label} stdout must contain an object"
        )
    payload = dict(value)
    payload["returncode"] = return_code
    if return_code != 0 and payload.get("valid") is True:
        raise GitHubResearchLovePrepareOnceError(
            f"{label} returned {return_code} despite valid=true"
        )
    return payload


def _blocked(
    *,
    mode: str,
    status: str,
    issues: Sequence[str],
    scan: Mapping[str, Any] | None,
    runtime: Mapping[str, Any] | None,
    fetch: Mapping[str, Any] | None,
    prepared: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "valid": False,
        "mode": mode,
        "status": status,
        "issues": list(issues),
        "scan_configuration": scan,
        "runtime_readiness": runtime,
        "fetch_cycle": fetch,
        "prepared_cycle": prepared,
        "publication_plan_digest": "",
        "boundaries": _boundaries(
            execute=mode == "execute",
            fetch_performed=fetch is not None,
            prepare_performed=prepared is not None,
        ),
    }


def _issues(value: Mapping[str, Any]) -> list[str]:
    raw = value.get("issues")
    if not isinstance(raw, list):
        return ["child report did not provide an issues list"]
    return [str(item) for item in raw]


def _policy_decision_id(value: object) -> str:
    normalized = str(value).strip()
    if not normalized.startswith("policy:"):
        raise GitHubResearchLovePrepareOnceError(
            "policy-decision-id must start with policy:"
        )
    return normalized


def _require_effect_gate(name: str) -> None:
    enabled = os.environ.get(name, "").strip().casefold()
    if enabled not in {"1", "true", "yes", "on"}:
        raise GitHubResearchLovePrepareOnceError(
            f"missing explicit effect gate {name}"
        )


def _required_mapping(
    value: Mapping[str, Any],
    name: str,
) -> Mapping[str, Any]:
    candidate = value.get(name)
    if not isinstance(candidate, Mapping):
        raise GitHubResearchLovePrepareOnceError(
            f"{name} must be an object"
        )
    return candidate


def _required_text(
    value: Mapping[str, Any],
    name: str,
) -> str:
    candidate = value.get(name)
    if not isinstance(candidate, str) or not candidate.strip():
        raise GitHubResearchLovePrepareOnceError(
            f"{name} must not be empty"
        )
    return candidate.strip()


def _absolute_input(path: Path) -> Path:
    return path if path.is_absolute() else (_REPO_ROOT / path).resolve()


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


def _boundaries(
    *,
    execute: bool,
    fetch_performed: bool,
    prepare_performed: bool,
) -> dict[str, object]:
    return {
        "operator_entrypoint_only": True,
        "existing_scan_config_builder_reused": True,
        "existing_runtime_readiness_reused": True,
        "existing_artifact_fetch_reused": True,
        "existing_closed_loop_prepare_reused": True,
        "new_scheduler_created": False,
        "new_dispatcher_created": False,
        "new_sql_store_created": False,
        "new_qdrant_client_created": False,
        "new_openvino_runtime_created": False,
        "new_laboratory_provider_created": False,
        "remote_issue_mutation_performed": False,
        "project_v2_mutation_performed": False,
        "artifact_fetch_performed": fetch_performed,
        "local_prepare_performed": prepare_performed,
        "sql_write_possible": execute and prepare_performed,
        "qdrant_write_possible": execute and prepare_performed,
        "operator_confirmation_required": prepare_performed,
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
                    "prepared_output="
                    f"{payload.get('prepared_output', '')}"
                ),
            )
        )
    )
    for issue in payload.get("issues", ()):
        print(f"issue: {issue}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
