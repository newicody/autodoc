#!/usr/bin/env python3
"""Build/install the attachment-manifest bootstrap files for the external idea repo.

0170 is local-only: no GitHub API call and no remote mutation. It copies the
attachment workflow/script templates into a staging directory or into an
explicitly supplied local clone of the external idea repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE_ROOT = _REPO_ROOT / "templates" / "github"
_DEVELOPMENT_REPOSITORY = "newicody/autodoc"
_SCHEMA = "missipy.github_idea_repo.attachment_bootstrap_bundle.v1"
_TEMPLATE_MAP: tuple[tuple[str, str], ...] = (
    ("autodoc-attachment-manifest.yml", ".github/workflows/autodoc-attachment-manifest.yml"),
    ("scripts/build_autodoc_issue_attachment_manifest.py", "scripts/build_autodoc_issue_attachment_manifest.py"),
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build/install attachment-manifest templates for the external idea repository.")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path(".var/bootstrap/autodoc-ideas-attachments"))
    parser.add_argument("--external-repo-root", type=Path, default=None)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    report = build_attachment_bootstrap_bundle(args.repository, args.output_dir, args.external_repo_root, args.write)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        for item in report["files"]:
            state = "written" if item["external_written"] else "staged"
            print(f"{state}: {item['target_path']}")
    return 0 if report["status"] == "ok" else 1


def build_attachment_bootstrap_bundle(repository: str, output_dir: Path, external_repo_root: Path | None, write: bool) -> dict[str, Any]:
    issues = _validate(repository, external_repo_root, write)
    files: list[dict[str, Any]] = []
    if not issues:
        for source_rel, target_rel in _TEMPLATE_MAP:
            source_path = _TEMPLATE_ROOT / source_rel
            if not source_path.exists():
                issues.append({"code": "template_missing", "message": str(source_path)})
                continue
            payload = source_path.read_bytes()
            staged_path = _safe_join(output_dir, target_rel)
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            staged_path.write_bytes(payload)
            external_path = None
            external_written = False
            if write and external_repo_root is not None:
                external_path = _safe_join(external_repo_root, target_rel)
                external_path.parent.mkdir(parents=True, exist_ok=True)
                external_path.write_bytes(payload)
                external_written = True
            files.append({
                "source_template": str(source_path.relative_to(_REPO_ROOT)),
                "target_path": target_rel,
                "staged_path": str(staged_path),
                "external_path": str(external_path) if external_path is not None else None,
                "external_written": external_written,
                "byte_count": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            })
    report = {
        "schema": _SCHEMA,
        "status": "ok" if not issues else "blocked",
        "repository": repository,
        "output_dir": str(output_dir),
        "external_repo_root": str(external_repo_root) if external_repo_root else None,
        "write_requested": write,
        "github_api_called": False,
        "remote_mutation_performed": False,
        "files": files,
        "issues": issues,
        "boundary": [
            "external idea repository attachment bootstrap",
            "reuse 0166 external action pattern",
            "no GitHub API call",
            "no remote mutation",
            "GitHub Actions artifacts remain the source system",
            "no user artifacts in Autodoc repository",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "autodoc_idea_repo_attachment_bootstrap_manifest.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _validate(repository: str, external_repo_root: Path | None, write: bool) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not repository or "/" not in repository:
        issues.append({"code": "repository_invalid", "message": "repository must be owner/name"})
    if repository == _DEVELOPMENT_REPOSITORY:
        issues.append({"code": "development_repository_rejected", "message": "target must be the external idea repository"})
    if write and external_repo_root is None:
        issues.append({"code": "external_repo_root_required", "message": "--write requires --external-repo-root"})
    return issues


def _safe_join(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    root_resolved = root.resolve()
    if root_resolved != candidate and root_resolved not in candidate.parents:
        raise ValueError(f"path escapes output root: {relative}")
    return candidate


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
