#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


_REPORT_SCHEMA = "missipy.docs_svg_build_policy_report.v1"


@dataclass(frozen=True)
class DocsSvgBuildPolicyEntry:
    path: Path
    policy: str
    action: str

    def to_json_dict(self, root: Path) -> dict[str, object]:
        return {
            "path": self.path.resolve().relative_to(root.resolve()).as_posix(),
            "policy": self.policy,
            "action": self.action,
        }


@dataclass(frozen=True)
class DocsSvgBuildPolicyReport:
    root: Path
    architecture_root: Path
    checked_svg_count: int
    source_only_svg_count: int
    removed_svg_count: int
    publishable_svg_count: int
    entries: tuple[DocsSvgBuildPolicyEntry, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _REPORT_SCHEMA,
            "root": str(self.root),
            "architecture_root": str(self.architecture_root),
            "checked_svg_count": self.checked_svg_count,
            "source_only_svg_count": self.source_only_svg_count,
            "removed_svg_count": self.removed_svg_count,
            "publishable_svg_count": self.publishable_svg_count,
            "entries": [entry.to_json_dict(self.root) for entry in self.entries],
        }


def build_docs_svg_build_policy_report(
    root: Path,
    *,
    clean: bool = False,
    architecture_root: Path | None = None,
) -> DocsSvgBuildPolicyReport:
    """Apply the repository SVG build policy.

    Global Graphviz builds may create SVG files for every DOT source. Context
    architecture diagrams are intentionally source-only in this repository, so
    generated SVGs under ``doc/docs/architecture/context`` must be removed before
    rule tests run.
    """

    root = root.resolve()
    if architecture_root is None:
        architecture_root = root / "doc" / "docs" / "architecture"
    elif not architecture_root.is_absolute():
        architecture_root = root / architecture_root
    architecture_root = architecture_root.resolve()

    entries: list[DocsSvgBuildPolicyEntry] = []
    checked = 0
    source_only = 0
    removed = 0
    publishable = 0

    for svg_path in sorted(architecture_root.rglob("*.svg")):
        checked += 1
        if is_source_only_svg(svg_path, root=root):
            source_only += 1
            action = "remove" if clean else "would_remove"
            if clean:
                svg_path.unlink()
                removed += 1
            entries.append(
                DocsSvgBuildPolicyEntry(
                    path=svg_path,
                    policy="source-only",
                    action=action,
                )
            )
        else:
            publishable += 1
            entries.append(
                DocsSvgBuildPolicyEntry(
                    path=svg_path,
                    policy="publishable",
                    action="keep",
                )
            )

    return DocsSvgBuildPolicyReport(
        root=root,
        architecture_root=architecture_root,
        checked_svg_count=checked,
        source_only_svg_count=source_only,
        removed_svg_count=removed,
        publishable_svg_count=publishable,
        entries=tuple(entries),
    )


def is_source_only_svg(path: Path, *, root: Path) -> bool:
    path = path.resolve()
    root = root.resolve()
    context_root = root / "doc" / "docs" / "architecture" / "context"
    try:
        path.relative_to(context_root)
    except ValueError:
        return False
    return path.suffix == ".svg"


def assert_docs_svg_build_policy(report: DocsSvgBuildPolicyReport) -> None:
    remaining = [
        entry.path.resolve().relative_to(report.root.resolve()).as_posix()
        for entry in report.entries
        if entry.policy == "source-only" and entry.path.exists()
    ]
    if remaining:
        raise AssertionError(
            "source-only SVG files remain after documentation SVG policy check:\n"
            + "\n".join(remaining)
        )


def write_docs_svg_build_policy_report(path: Path, report: DocsSvgBuildPolicyReport) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def render_docs_svg_build_policy_report(report: DocsSvgBuildPolicyReport) -> str:
    lines = [
        "documentation svg build policy",
        f"root: {report.root}",
        f"architecture_root: {report.architecture_root}",
        f"checked_svg_count: {report.checked_svg_count}",
        f"source_only_svg_count: {report.source_only_svg_count}",
        f"removed_svg_count: {report.removed_svg_count}",
        f"publishable_svg_count: {report.publishable_svg_count}",
    ]
    for entry in report.entries:
        relative = entry.path.resolve().relative_to(report.root.resolve()).as_posix()
        lines.append(f"- {entry.action}: {relative} [{entry.policy}]")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean or check generated documentation SVG files.")
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    parser.add_argument(
        "--architecture-root",
        type=Path,
        default=Path("doc/docs/architecture"),
        help="architecture root relative to repository root",
    )
    parser.add_argument("--clean", action="store_true", help="remove source-only SVG files")
    parser.add_argument("--check", action="store_true", help="fail if source-only SVG files remain")
    parser.add_argument(
        "--report-file",
        type=Path,
        default=Path("doc/maintenance/docs_svg_build_policy_report.json"),
        help="JSON report path",
    )
    args = parser.parse_args()

    report = build_docs_svg_build_policy_report(
        args.root,
        clean=args.clean,
        architecture_root=args.architecture_root,
    )
    write_docs_svg_build_policy_report(args.report_file, report)
    print(render_docs_svg_build_policy_report(report))

    if args.check:
        assert_docs_svg_build_policy(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
