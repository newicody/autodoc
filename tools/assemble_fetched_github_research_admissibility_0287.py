#!/usr/bin/env python3
"""Load fetched ready_runs, assemble their triplets, and evaluate admissibility.

This filesystem adapter consumes the persisted report produced by
``run_github_actions_artifact_fetch_once_0287.py``.  It reads only local
artifact files and delegates every semantic decision to existing context
contracts.  It does not write SQL or Qdrant, mutate GitHub, create a Scheduler
command, or execute a laboratory.
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

from context.github_ready_run_research_admissibility_0287 import (  # noqa: E402
    GitHubReadyRunArtifactContent,
    GitHubReadyRunResearchAdmissibilityCommand,
    assemble_ready_run_and_evaluate_research_admissibility,
)

SCHEMA = "missipy.github.fetched_research_admissibility_report.v1"
_FETCH_CYCLE_SCHEMA = "missipy.github_actions.artifact_fetch_cycle_once.v1"
_SCAN_SCHEMA = "missipy.github_actions.artifact_scan_once_live.v1"
_EXPECTED_FILES = {
    "authoritative_request": "authoritative_request.json",
    "copilot_advisory": "copilot_advisory.json",
    "run_manifest": "dual_artifact_manifest.json",
}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Assemble locally fetched GitHub research artifacts and evaluate "
            "their admissibility without scheduling a laboratory."
        )
    )
    parser.add_argument("--fetch-cycle-report", type=Path, required=True)
    parser.add_argument("--run-id", action="append", default=[])
    parser.add_argument("--state-path", type=Path)
    parser.add_argument("--max-artifact-bytes", type=int, default=5 * 1024 * 1024)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    report_path = _absolute_input(args.fetch_cycle_report)
    issues: list[str] = []
    if args.max_artifact_bytes <= 0:
        issues.append("max-artifact-bytes must be > 0")
    cycle = _read_json_mapping(report_path, "fetch cycle report", issues)
    if cycle:
        if cycle.get("schema") != _FETCH_CYCLE_SCHEMA:
            issues.append("fetch cycle report schema mismatch")
        if cycle.get("valid") is not True:
            issues.append("fetch cycle report must be valid")
        if cycle.get("mode") != "execute":
            issues.append("fetch cycle report must come from execute mode")
        if cycle.get("status") != "artifacts-fetched":
            issues.append("fetch cycle status must be artifacts-fetched")

    scan_path = _scan_report_path(cycle, report_path, issues)
    scan = (
        _read_json_mapping(scan_path, "artifact scan report", issues)
        if scan_path is not None
        else {}
    )
    if scan:
        if scan.get("schema") != _SCAN_SCHEMA:
            issues.append("artifact scan report schema mismatch")
        if scan.get("valid") is not True:
            issues.append("artifact scan report must be valid")

    state_path = _resolve_state_path(args.state_path, scan, report_path)
    state = (
        _read_json_mapping(state_path, "artifact fetch state", issues)
        if state_path is not None and state_path.is_file()
        else {}
    )

    selected_run_ids = tuple(dict.fromkeys(str(value).strip() for value in args.run_id))
    if any(not value for value in selected_run_ids):
        issues.append("run-id must not be empty")
    ready_runs = _ready_runs(cycle, scan, selected_run_ids, issues)

    results: list[dict[str, Any]] = []
    if not issues:
        for ready_run in ready_runs:
            loaded, load_issues = _load_ready_run_contents(
                ready_run,
                state=state,
                max_artifact_bytes=args.max_artifact_bytes,
            )
            if load_issues:
                results.append(
                    {
                        "valid": False,
                        "admissible": False,
                        "status": "artifact-load-invalid",
                        "issues": load_issues,
                        "repository": ready_run.get("repository", ""),
                        "run_id": ready_run.get("run_id", ""),
                        "scheduler_command_created": False,
                        "laboratory_execution_started": False,
                    }
                )
                continue
            result = assemble_ready_run_and_evaluate_research_admissibility(
                GitHubReadyRunResearchAdmissibilityCommand(
                    ready_run=ready_run,
                    artifact_contents=tuple(loaded),
                )
            )
            results.append(result.to_mapping())

    valid = not issues and all(item.get("valid") is True for item in results)
    admissible_count = sum(1 for item in results if item.get("admissible") is True)
    payload = {
        "schema": SCHEMA,
        "valid": valid,
        "status": (
            "rejected"
            if issues
            else "evaluated"
            if results
            else "nothing-ready"
        ),
        "issues": issues,
        "fetch_cycle_report": str(report_path),
        "artifact_scan_report": "" if scan_path is None else str(scan_path),
        "state_path": "" if state_path is None else str(state_path),
        "selected_run_ids": list(selected_run_ids),
        "counts": {
            "ready_run_count": len(ready_runs),
            "evaluated_count": len(results),
            "admissible_count": admissible_count,
            "inadmissible_count": len(results) - admissible_count,
        },
        "results": results,
        "boundaries": {
            "local_artifact_read_only": True,
            "existing_ready_runs_reused": True,
            "existing_dual_artifact_assembly_reused": True,
            "existing_correlated_work_package_reused": True,
            "existing_admissibility_gate_reused": True,
            "filesystem_write_performed": args.output is not None,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "github_mutation_performed": False,
            "scheduler_command_created": False,
            "scheduler_dispatch_started": False,
            "laboratory_execution_started": False,
        },
    }
    if args.output is not None:
        _write_json_atomic(_absolute_output(args.output), payload)
    _emit(payload, args.format)
    return 0 if valid else 2


def _ready_runs(
    cycle: Mapping[str, Any],
    scan: Mapping[str, Any],
    selected_run_ids: tuple[str, ...],
    issues: list[str],
) -> list[Mapping[str, Any]]:
    source = cycle.get("ready_runs")
    if not isinstance(source, list):
        source = scan.get("ready_runs")
    if not isinstance(source, list):
        issues.append("ready_runs must be a list")
        return []
    runs = [dict(item) for item in source if isinstance(item, Mapping)]
    if selected_run_ids:
        by_id = {str(item.get("run_id", "")).strip(): item for item in runs}
        missing = [run_id for run_id in selected_run_ids if run_id not in by_id]
        if missing:
            issues.append("requested run_id not ready: " + ", ".join(missing))
        return [by_id[run_id] for run_id in selected_run_ids if run_id in by_id]
    return runs


def _load_ready_run_contents(
    ready_run: Mapping[str, Any],
    *,
    state: Mapping[str, Any],
    max_artifact_bytes: int,
) -> tuple[list[GitHubReadyRunArtifactContent], list[str]]:
    issues: list[str] = []
    loaded: list[GitHubReadyRunArtifactContent] = []
    artifacts = ready_run.get("artifacts")
    if not isinstance(artifacts, Mapping):
        return [], ["ready_run artifacts must be a mapping"]
    for role, filename in _EXPECTED_FILES.items():
        record = artifacts.get(role)
        if not isinstance(record, Mapping):
            issues.append(f"ready_run artifact role missing: {role}")
            continue
        staging_dir = _staging_dir(record, state)
        if staging_dir is None:
            issues.append(f"{role} staging directory is unavailable")
            continue
        file_path, file_issues = _find_one_regular_file(staging_dir, filename)
        issues.extend(f"{role}: {issue}" for issue in file_issues)
        if file_path is None:
            continue
        size = file_path.stat().st_size
        if size <= 0:
            issues.append(f"{role}: artifact file is empty")
            continue
        if size > max_artifact_bytes:
            issues.append(
                f"{role}: artifact file exceeds max-artifact-bytes ({size})"
            )
            continue
        loaded.append(
            GitHubReadyRunArtifactContent(
                role=role,
                content=file_path.read_bytes(),
                artifact_id=str(record.get("artifact_id", "")),
                source_artifact_name=str(record.get("artifact_name", "")),
            )
        )
    return loaded, issues


def _staging_dir(
    record: Mapping[str, Any],
    state: Mapping[str, Any],
) -> Path | None:
    direct = str(record.get("staging_dir", "")).strip()
    if direct:
        return _absolute_input(Path(direct))
    artifacts = state.get("artifacts")
    if not isinstance(artifacts, Mapping):
        return None
    artifact_id = str(record.get("artifact_id", "")).strip()
    run_id = str(record.get("run_id", "")).strip()
    artifact_name = str(record.get("artifact_name", "")).strip()
    matches: list[Path] = []
    for value in artifacts.values():
        if not isinstance(value, Mapping):
            continue
        if str(value.get("artifact_id", "")).strip() != artifact_id:
            continue
        if str(value.get("run_id", "")).strip() != run_id:
            continue
        if str(value.get("artifact_name", "")).strip() != artifact_name:
            continue
        staging = str(value.get("staging_dir", "")).strip()
        if staging:
            matches.append(_absolute_input(Path(staging)))
    unique = tuple(dict.fromkeys(matches))
    return unique[0] if len(unique) == 1 else None


def _find_one_regular_file(
    staging_dir: Path,
    filename: str,
) -> tuple[Path | None, list[str]]:
    issues: list[str] = []
    if not staging_dir.is_dir():
        return None, [f"staging directory not found: {staging_dir}"]
    root = staging_dir.resolve()
    matches: list[Path] = []
    for candidate in staging_dir.rglob(filename):
        if candidate.is_symlink():
            issues.append(f"symbolic link is not allowed: {candidate}")
            continue
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            issues.append(f"cannot resolve artifact file: {exc}")
            continue
        if root not in resolved.parents:
            issues.append(f"artifact file escapes staging directory: {candidate}")
            continue
        if resolved.is_file():
            matches.append(resolved)
    unique = tuple(dict.fromkeys(matches))
    if len(unique) != 1:
        issues.append(
            f"expected exactly one {filename}, found {len(unique)}"
        )
        return None, issues
    return unique[0], issues


def _scan_report_path(
    cycle: Mapping[str, Any],
    cycle_path: Path,
    issues: list[str],
) -> Path | None:
    reports = cycle.get("reports")
    raw = reports.get("artifact_scan") if isinstance(reports, Mapping) else None
    if not isinstance(raw, str) or not raw.strip():
        issues.append("fetch cycle report does not reference artifact scan report")
        return None
    path = Path(raw.strip())
    if not path.is_absolute():
        path = cycle_path.parent / path
    return path.resolve()


def _resolve_state_path(
    explicit: Path | None,
    scan: Mapping[str, Any],
    cycle_path: Path,
) -> Path | None:
    if explicit is not None:
        return _absolute_input(explicit)
    raw = scan.get("state_path")
    if not isinstance(raw, str) or not raw.strip():
        return None
    path = Path(raw.strip())
    if not path.is_absolute():
        path = cycle_path.parent / path
    return path.resolve()


def _read_json_mapping(
    path: Path,
    label: str,
    issues: list[str],
) -> dict[str, Any]:
    if not path.is_file():
        issues.append(f"{label} not found: {path}")
        return {}
    try:
        decoded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"{label} is unreadable: {exc}")
        return {}
    if not isinstance(decoded, Mapping):
        issues.append(f"{label} must contain a JSON object")
        return {}
    return dict(decoded)


def _absolute_input(path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (_REPO_ROOT / path).resolve()


def _absolute_output(path: Path) -> Path:
    return path if path.is_absolute() else _REPO_ROOT / path


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _emit(payload: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return
    counts = payload.get("counts")
    counts = counts if isinstance(counts, Mapping) else {}
    print(
        " ".join(
            (
                f"valid={payload.get('valid')}",
                f"status={payload.get('status')}",
                f"ready={counts.get('ready_run_count', 0)}",
                f"evaluated={counts.get('evaluated_count', 0)}",
                f"admissible={counts.get('admissible_count', 0)}",
                "scheduler_command_created=false",
                "laboratory_execution_started=false",
            )
        )
    )
    for issue in payload.get("issues", []):
        print(f"issue: {issue}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
