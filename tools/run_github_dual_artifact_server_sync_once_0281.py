#!/usr/bin/env python3
"""Compose the existing 0167 sync with 0281 run-level dual-artifact intake.

The existing 0168 fetcher already exposes ``--sync-tool``. This adapter is
selected through that port. It preserves the raw per-artifact server dataset
sync, then inspects the sibling staging directories for the same Actions run
and delegates semantic correlation to the pure 0281-r2 assembly contract.

It performs no network call and no GitHub, SQL, Qdrant or Scheduler mutation.
"""

from __future__ import annotations

import argparse
import configparser
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_dual_artifact_run_assembly_0281 import (  # noqa: E402
    GitHubDualArtifactRunAssemblyCommand,
    GitHubDualArtifactRunMember,
    run_github_dual_artifact_run_assembly,
)

_SCHEMA = "missipy.github.dual_artifact_server_sync_once.v1"
_RUN_GROUP_SCHEMA = "missipy.github.dual_artifact_fetch_run_group.v1"
_DEFAULT_BASE_SYNC_TOOL = Path("tools/run_github_artifact_server_sync_once.py")
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_EXPECTED_ARTIFACT_BY_FILENAME = {
    "authoritative_request.json": "autodoc-authoritative-request",
    "copilot_advisory.json": "autodoc-copilot-advisory",
    "dual_artifact_manifest.json": "autodoc-dual-artifact-manifest",
}


@dataclass(frozen=True, slots=True)
class IntegrationSettings:
    repository: str
    dataset_root: Path
    report_root: Path
    base_sync_tool: Path


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the existing server dataset sync, then assemble correlated "
            "dual artifacts already staged for the same GitHub Actions run."
        )
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--repository", default="")
    parser.add_argument(
        "--base-sync-tool",
        type=Path,
        default=_DEFAULT_BASE_SYNC_TOOL,
    )
    parser.add_argument("--report-root", type=Path, default=None)
    parser.add_argument("--no-run-report-write", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    settings = _load_settings(args)
    _validate_inputs(args, settings)

    raw_sync = _run_base_sync(
        settings.base_sync_tool,
        args.config,
        args.artifact_dir,
        str(args.run_id),
        str(args.artifact_id),
    )
    raw_status = str(raw_sync.get("status", "unknown"))
    if raw_status != "ok":
        report = {
            "schema": _SCHEMA,
            "status": raw_status,
            "raw_sync": dict(raw_sync),
            "repository": settings.repository,
            "run_id": str(args.run_id),
            "artifact_id": str(args.artifact_id),
            "run_group": {},
            "run_group_write_action": "not_attempted",
            "vispy_event_path": raw_sync.get("vispy_event_path"),
            "boundary": _boundary(),
        }
        _emit(report, args.format)
        return 1

    run_root = args.artifact_dir.resolve().parent
    run_group = _build_run_group(
        repository=settings.repository,
        run_id=str(args.run_id),
        run_root=run_root,
    )

    write_action = "disabled"
    effective_run_group = run_group
    report_path = settings.report_root / _repository_slug(settings.repository) / (
        f"{args.run_id}.json"
    )
    if not args.no_run_report_write:
        write_action, effective_run_group = _persist_run_report(
            report_path,
            run_group,
        )

    report = {
        "schema": _SCHEMA,
        "status": "ok",
        "raw_sync": dict(raw_sync),
        "repository": settings.repository,
        "run_id": str(args.run_id),
        "artifact_id": str(args.artifact_id),
        "artifact_dir": str(args.artifact_dir.resolve()),
        "run_root": str(run_root),
        "run_group": effective_run_group,
        "run_group_candidate": (
            run_group if write_action == "collision" else {}
        ),
        "run_group_write_action": write_action,
        "run_group_report_path": str(report_path),
        "vispy_event_path": raw_sync.get("vispy_event_path"),
        "boundary": _boundary(),
    }
    _emit(report, args.format)
    return 0


def _load_settings(args: argparse.Namespace) -> IntegrationSettings:
    parser = configparser.ConfigParser()
    loaded = parser.read(args.config, encoding="utf-8")
    if not loaded:
        raise SystemExit(f"config not found: {args.config}")

    source = parser["artifact_source"] if parser.has_section("artifact_source") else {}
    dataset = parser["server_dataset"] if parser.has_section("server_dataset") else {}
    if not dataset and parser.has_section("dataset"):
        dataset = parser["dataset"]

    repositories = _list_value(source.get("repositories", ""))
    repository = str(args.repository).strip() or (
        repositories[0] if repositories else ""
    )
    dataset_root = Path(
        str(
            dataset.get("root")
            or dataset.get("dataset_root")
            or ".var/server_datasets/github_artifacts"
        )
    ).expanduser()
    report_root = (
        args.report_root
        if args.report_root is not None
        else dataset_root / "index" / "github_dual_artifact_run_groups"
    )
    return IntegrationSettings(
        repository=repository,
        dataset_root=dataset_root,
        report_root=report_root,
        base_sync_tool=args.base_sync_tool,
    )


def _validate_inputs(
    args: argparse.Namespace,
    settings: IntegrationSettings,
) -> None:
    if not _REPOSITORY.fullmatch(settings.repository):
        raise SystemExit("repository must be configured as owner/name")
    if not str(args.run_id).strip():
        raise SystemExit("run-id must not be empty")
    if not str(args.artifact_id).strip():
        raise SystemExit("artifact-id must not be empty")
    if not args.artifact_dir.exists() or not args.artifact_dir.is_dir():
        raise SystemExit(f"artifact-dir is not a directory: {args.artifact_dir}")
    if args.artifact_dir.is_symlink():
        raise SystemExit("artifact-dir must not be a symbolic link")
    if settings.base_sync_tool.resolve() == Path(__file__).resolve():
        raise SystemExit("base-sync-tool must not point to this adapter")


def _run_base_sync(
    base_sync_tool: Path,
    config_path: Path,
    artifact_dir: Path,
    run_id: str,
    artifact_id: str,
) -> Mapping[str, Any]:
    command = [
        sys.executable,
        str(base_sync_tool),
        "--config",
        str(config_path),
        "--artifact-dir",
        str(artifact_dir),
        "--run-id",
        run_id,
        "--artifact-id",
        artifact_id,
        "--format",
        "json",
    ]
    completed = subprocess.run(
        command,
        cwd=_REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "base sync tool did not return a JSON object"
        ) from exc
    if not isinstance(payload, Mapping):
        raise RuntimeError("base sync tool JSON must be an object")
    if completed.returncode != 0 and payload.get("status") == "ok":
        raise RuntimeError(
            "base sync tool returned non-zero with status=ok"
        )
    return payload


def _build_run_group(
    *,
    repository: str,
    run_id: str,
    run_root: Path,
) -> dict[str, Any]:
    members, collected_files, collection_issues = _collect_run_members(run_root)
    filenames = {member.filename for member in members}

    missing = [
        filename
        for filename in (
            "authoritative_request.json",
            "dual_artifact_manifest.json",
        )
        if filename not in filenames
    ]
    if collection_issues:
        return _run_group_mapping(
            repository=repository,
            run_id=run_id,
            run_root=run_root,
            status="blocked",
            issues=collection_issues,
            collected_files=collected_files,
        )
    if missing:
        return _run_group_mapping(
            repository=repository,
            run_id=run_id,
            run_root=run_root,
            status="pending",
            issues=tuple(f"waiting for {filename}" for filename in missing),
            collected_files=collected_files,
        )

    manifest_members = [
        member
        for member in members
        if member.filename == "dual_artifact_manifest.json"
    ]
    if len(manifest_members) != 1:
        return _run_group_mapping(
            repository=repository,
            run_id=run_id,
            run_root=run_root,
            status="blocked",
            issues=("manifest member must be unique",),
            collected_files=collected_files,
        )

    try:
        manifest = json.loads(manifest_members[0].content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _run_group_mapping(
            repository=repository,
            run_id=run_id,
            run_root=run_root,
            status="blocked",
            issues=(f"manifest is not valid UTF-8 JSON: {type(exc).__name__}",),
            collected_files=collected_files,
        )
    if not isinstance(manifest, Mapping):
        return _run_group_mapping(
            repository=repository,
            run_id=run_id,
            run_root=run_root,
            status="blocked",
            issues=("manifest JSON must be an object",),
            collected_files=collected_files,
        )

    advisory_expected = bool(
        manifest.get("advisory_filename")
        or manifest.get("advisory_artifact_ref")
        or manifest.get("advisory_sha256")
    )
    if advisory_expected and "copilot_advisory.json" not in filenames:
        return _run_group_mapping(
            repository=repository,
            run_id=run_id,
            run_root=run_root,
            status="pending",
            issues=("waiting for copilot_advisory.json",),
            collected_files=collected_files,
        )

    result = run_github_dual_artifact_run_assembly(
        GitHubDualArtifactRunAssemblyCommand(
            repository=repository,
            run_id=run_id,
            members=tuple(members),
        )
    )
    result_mapping = result.to_mapping()
    return _run_group_mapping(
        repository=repository,
        run_id=run_id,
        run_root=run_root,
        status="ready" if result.valid else "blocked",
        issues=tuple(result.issues),
        collected_files=collected_files,
        assembly=result_mapping,
    )


def _collect_run_members(
    run_root: Path,
) -> tuple[
    list[GitHubDualArtifactRunMember],
    list[dict[str, Any]],
    tuple[str, ...],
]:
    root = run_root.resolve()
    members: list[GitHubDualArtifactRunMember] = []
    collected: list[dict[str, Any]] = []
    issues: list[str] = []

    if not root.exists() or not root.is_dir():
        return members, collected, ("run staging root is missing",)

    for artifact_dir in sorted(root.iterdir(), key=lambda item: item.name):
        if artifact_dir.is_symlink():
            issues.append(f"symbolic-link artifact directory rejected: {artifact_dir.name}")
            continue
        if not artifact_dir.is_dir():
            continue
        artifact_root = artifact_dir.resolve()
        for path in sorted(artifact_dir.rglob("*"), key=lambda item: str(item)):
            if path.is_symlink():
                issues.append(
                    f"symbolic-link artifact member rejected: "
                    f"{path.relative_to(root)}"
                )
                continue
            if not path.is_file():
                continue
            artifact_name = _EXPECTED_ARTIFACT_BY_FILENAME.get(path.name)
            if artifact_name is None:
                continue
            resolved = path.resolve()
            if not resolved.is_relative_to(artifact_root):
                issues.append(
                    f"artifact member escaped staging directory: "
                    f"{path.relative_to(root)}"
                )
                continue
            content = path.read_bytes()
            members.append(
                GitHubDualArtifactRunMember(
                    artifact_name=artifact_name,
                    filename=path.name,
                    content=content,
                )
            )
            collected.append(
                {
                    "artifact_name": artifact_name,
                    "filename": path.name,
                    "relative_path": str(path.relative_to(root)),
                    "size_bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )
    return members, collected, tuple(dict.fromkeys(issues))


def _run_group_mapping(
    *,
    repository: str,
    run_id: str,
    run_root: Path,
    status: str,
    issues: tuple[str, ...],
    collected_files: list[dict[str, Any]],
    assembly: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": _RUN_GROUP_SCHEMA,
        "status": status,
        "repository": repository,
        "run_id": run_id,
        "run_root": str(run_root.resolve()),
        "issues": list(issues),
        "collected_files": collected_files,
        "assembly": dict(assembly or {}),
        "advisory_payload_retained": bool(
            assembly
            and isinstance(assembly.get("intake"), Mapping)
            and assembly["intake"].get("advisory")
        ),
        "advisory_content_authoritative": False,
        "scheduler_route_created": False,
        "sql_write_performed": False,
        "qdrant_write_performed": False,
        "github_mutation_performed": False,
    }


def _persist_run_report(
    path: Path,
    candidate: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate_mapping = dict(candidate)
    candidate_bytes = _canonical_json_bytes(candidate_mapping)

    if not path.exists():
        path.write_bytes(candidate_bytes)
        return "created", candidate_mapping

    existing = _read_json_mapping(path)
    existing_bytes = _canonical_json_bytes(existing)
    if existing_bytes == candidate_bytes:
        return "replayed", existing

    existing_status = str(existing.get("status", "unknown"))
    if existing_status in {"ready", "blocked"}:
        return "collision", existing

    path.write_bytes(candidate_bytes)
    return "updated", candidate_mapping


def _read_json_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise RuntimeError(f"run-group report must be a JSON object: {path}")
    return dict(payload)


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _repository_slug(repository: str) -> str:
    return repository.replace("/", "__")


def _list_value(value: object) -> list[str]:
    return [
        item.strip()
        for item in str(value or "").replace("\n", ",").split(",")
        if item.strip()
    ]


def _boundary() -> list[str]:
    return [
        "reuses the existing 0168 --sync-tool port",
        "calls the existing 0167 server dataset sync first",
        "reads only already-downloaded sibling staging directories",
        "retains Copilot advisory as non-authoritative intake content",
        "writes only a local idempotent run-group report",
        "no network call",
        "no GitHub mutation",
        "no SQL write",
        "no Qdrant write",
        "no Scheduler route",
    ]


def _emit(report: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return
    run_group = report.get("run_group", {})
    semantic_status = (
        run_group.get("status", "unknown")
        if isinstance(run_group, Mapping)
        else "unknown"
    )
    print(f"status: {report.get('status', 'unknown')}")
    print(f"run_group_status: {semantic_status}")
    print(f"run_group_write_action: {report.get('run_group_write_action')}")
    print(f"run_group_report_path: {report.get('run_group_report_path')}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
