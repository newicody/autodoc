#!/usr/bin/env python3
"""Build a local bootstrap bundle for the external GitHub idea repository.

0169 installs/copies the GitHub Action templates prepared by 0166 into a local
staging directory or an explicitly supplied local clone of the external idea
repository. It performs no GitHub API call and no remote mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any, Mapping, Sequence


_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE_ROOT = _REPO_ROOT / "templates" / "github"
_DEVELOPMENT_REPOSITORY = "newicody/autodoc"
_SCHEMA = "missipy.github_idea_repo.bootstrap_bundle.v1"

_TEMPLATE_MAP: tuple[tuple[str, str], ...] = (
    ("autodoc-ticket-artifact.yml", ".github/workflows/autodoc-ticket-artifact.yml"),
    ("ISSUE_TEMPLATE/autodoc_task.yml", ".github/ISSUE_TEMPLATE/autodoc_task.yml"),
    ("scripts/build_autodoc_ticket_artifact.py", "scripts/build_autodoc_ticket_artifact.py"),
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build or install the local bootstrap files for the external GitHub idea repository."
    )
    parser.add_argument("--repository", required=True, help="External idea repository, for example newicody/autodoc-ideas")
    parser.add_argument("--project-url", required=True, help="GitHub Project URL associated with the idea workflow")
    parser.add_argument("--output-dir", type=Path, default=Path(".var/bootstrap/autodoc-ideas"))
    parser.add_argument("--external-repo-root", type=Path, default=None)
    parser.add_argument("--write", action="store_true", help="Also copy files into --external-repo-root")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    report = build_bootstrap_bundle(
        repository=args.repository,
        project_url=args.project_url,
        output_dir=args.output_dir,
        external_repo_root=args.external_repo_root,
        write=args.write,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        print(f"repository: {report['repository']}")
        print(f"output_dir: {report['output_dir']}")
        if report["external_repo_root"]:
            print(f"external_repo_root: {report['external_repo_root']}")
        for item in report["files"]:
            state = "written" if item["external_written"] else "staged"
            print(f"{state}: {item['target_path']}")
    return 0 if report["status"] == "ok" else 1


def build_bootstrap_bundle(
    *,
    repository: str,
    project_url: str,
    output_dir: Path,
    external_repo_root: Path | None,
    write: bool,
) -> dict[str, Any]:
    issues = _validate_request(repository=repository, project_url=project_url, external_repo_root=external_repo_root, write=write)
    if issues:
        return _report(
            status="blocked",
            repository=repository,
            project_url=project_url,
            output_dir=output_dir,
            external_repo_root=external_repo_root,
            write=write,
            files=[],
            issues=issues,
        )

    files: list[dict[str, Any]] = []
    for source_rel, target_rel in _TEMPLATE_MAP:
        source_path = _TEMPLATE_ROOT / source_rel
        if not source_path.exists():
            issues.append({"code": "template_missing", "message": str(source_path)})
            continue
        target_path = _safe_join(output_dir, target_rel)
        payload = source_path.read_bytes()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(payload)

        external_path = None
        external_written = False
        if write and external_repo_root is not None:
            external_path = _safe_join(external_repo_root, target_rel)
            external_path.parent.mkdir(parents=True, exist_ok=True)
            external_path.write_bytes(payload)
            external_written = True

        files.append(
            {
                "source_template": str(source_path.relative_to(_REPO_ROOT)),
                "target_path": target_rel,
                "staged_path": str(target_path),
                "external_path": str(external_path) if external_path is not None else None,
                "external_written": external_written,
                "byte_count": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    manifest_path = output_dir / "autodoc_idea_repo_bootstrap_manifest.json"
    report = _report(
        status="ok" if not issues else "blocked",
        repository=repository,
        project_url=project_url,
        output_dir=output_dir,
        external_repo_root=external_repo_root,
        write=write,
        files=files,
        issues=issues,
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report["manifest_path"] = str(manifest_path)
    return report


def _validate_request(
    *,
    repository: str,
    project_url: str,
    external_repo_root: Path | None,
    write: bool,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not repository or "/" not in repository:
        issues.append({"code": "repository_invalid", "message": "repository must be owner/name"})
    if repository == _DEVELOPMENT_REPOSITORY:
        issues.append({"code": "development_repository_rejected", "message": "bootstrap target must be the external idea repository"})
    if not project_url.startswith("https://github.com/"):
        issues.append({"code": "project_url_invalid", "message": "project-url must be a GitHub URL"})
    if write and external_repo_root is None:
        issues.append({"code": "external_repo_root_required", "message": "--write requires --external-repo-root"})
    return issues


def _report(
    *,
    status: str,
    repository: str,
    project_url: str,
    output_dir: Path,
    external_repo_root: Path | None,
    write: bool,
    files: list[Mapping[str, Any]],
    issues: list[Mapping[str, str]],
) -> dict[str, Any]:
    return {
        "schema": _SCHEMA,
        "status": status,
        "repository": repository,
        "project_url": project_url,
        "output_dir": str(output_dir),
        "external_repo_root": str(external_repo_root) if external_repo_root is not None else None,
        "write_requested": write,
        "github_api_called": False,
        "remote_mutation_performed": False,
        "files": list(files),
        "issues": list(issues),
        "boundary": [
            "reuse 0166 templates",
            "local bootstrap only",
            "no GitHub API call",
            "no remote mutation",
            "GitHub Actions artifacts remain the source system",
            "no user artifacts in Autodoc repository",
        ],
        "next_steps": [
            "review staged files",
            "copy or write them into the external idea repository",
            "commit and push from the external idea repository",
            "create or edit an issue to trigger the GitHub Action",
        ],
    }


def _safe_join(root: Path, relative_path: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe target path: {relative_path}")
    return root / relative


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
