#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class MarkdownMove:
    source: Path
    target: Path
    reason: str

    def to_json_dict(self, root: Path) -> dict[str, str]:
        return {
            "source": _rel(self.source, root),
            "target": _rel(self.target, root),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class MarkdownLayoutPlan:
    root: Path
    moves: tuple[MarkdownMove, ...]
    kept: tuple[Path, ...]
    skipped: tuple[Path, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": "missipy.markdown_doc_layout_plan.v1",
            "root": str(self.root),
            "move_count": len(self.moves),
            "kept_count": len(self.kept),
            "skipped_count": len(self.skipped),
            "moves": [move.to_json_dict(self.root) for move in self.moves],
            "kept": [_rel(path, self.root) for path in self.kept],
            "skipped": [_rel(path, self.root) for path in self.skipped],
        }


def build_markdown_layout_plan(root: Path) -> MarkdownLayoutPlan:
    root = root.resolve()
    moves: list[MarkdownMove] = []
    kept: list[Path] = []
    skipped: list[Path] = []

    for path in _markdown_files(root):
        rel = path.relative_to(root)

        if _is_skipped_path(rel):
            skipped.append(path)
            continue

        target, reason = classify_markdown_path(rel)
        if target is None:
            kept.append(path)
            continue

        absolute_target = root / target
        if absolute_target == path:
            kept.append(path)
            continue

        moves.append(MarkdownMove(source=path, target=absolute_target, reason=reason))

    return MarkdownLayoutPlan(
        root=root,
        moves=tuple(sorted(moves, key=lambda item: _rel(item.source, root))),
        kept=tuple(sorted(kept)),
        skipped=tuple(sorted(skipped)),
    )


def classify_markdown_path(rel: Path) -> tuple[Path | None, str]:
    parts = rel.parts

    if rel == Path("README.md"):
        return None, "root readme stays at repository root"

    if parts[0] == "doc":
        return _classify_doc_markdown(rel)

    if len(parts) == 1:
        name = rel.name
        phase = _phase_number(name)
        if name.startswith("MANIFEST"):
            return Path("doc/manifests") / name, "root manifest moved under doc/manifests"
        if name.startswith("CHANGELOG"):
            return Path("doc/changelogs") / name, "root changelog moved under doc/changelogs"
        if "CODE_RULE_ALIGNMENT" in name:
            return Path("doc/code-rules") / name, "code rule alignment moved under doc/code-rules"
        if phase is not None and _is_report_like(name):
            return Path("doc/reports") / f"phase{phase}" / name, "phase report moved under doc/reports"
        if name != "README.md":
            return Path("doc/reference/legacy") / name, "unclassified root markdown preserved as legacy reference"

    return None, "already scoped or unsupported location"


def apply_markdown_layout_plan(plan: MarkdownLayoutPlan) -> None:
    replacements = {
        _rel(move.source, plan.root): _rel(move.target, plan.root)
        for move in plan.moves
    }

    for move in plan.moves:
        move.target.parent.mkdir(parents=True, exist_ok=True)
        if move.target.exists():
            if move.source.read_bytes() == move.target.read_bytes():
                move.source.unlink()
                continue
            raise FileExistsError(f"target already exists and differs: {move.target}")
        move.source.rename(move.target)

    _rewrite_markdown_references(plan.root, replacements)


def write_markdown_layout_report(path: Path, plan: MarkdownLayoutPlan) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(plan.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def render_markdown_layout_plan(plan: MarkdownLayoutPlan) -> str:
    lines = [
        "markdown doc layout plan",
        f"root: {plan.root}",
        f"moves: {len(plan.moves)}",
        f"kept: {len(plan.kept)}",
        f"skipped: {len(plan.skipped)}",
    ]
    for move in plan.moves:
        lines.append(f"- {_rel(move.source, plan.root)} -> {_rel(move.target, plan.root)} [{move.reason}]")
    return "\n".join(lines)


def _classify_doc_markdown(rel: Path) -> tuple[Path | None, str]:
    if len(rel.parts) >= 2 and rel.parts[1] in {
        "releases",
        "docs",
        "reports",
        "manifests",
        "changelogs",
        "code-rules",
        "maintenance",
        "reference",
    }:
        return None, "already in documented doc namespace"

    name = rel.name
    phase = _phase_number(name)

    if len(rel.parts) == 2:
        if name.startswith("CHANGELOG"):
            return Path("doc/changelogs") / name, "doc changelog moved under doc/changelogs"
        if "CODE_RULE_ALIGNMENT" in name or name == "code_rule.md":
            return Path("doc/code-rules") / name, "code rule document moved under doc/code-rules"
        if name.startswith("MANIFEST"):
            return Path("doc/manifests") / name, "doc manifest moved under doc/manifests"
        if phase is not None and _is_report_like(name):
            return Path("doc/reports") / f"phase{phase}" / name, "doc phase report moved under doc/reports"

    return None, "doc markdown kept in current scoped location"


def _markdown_files(root: Path) -> Iterable[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if ".git" not in path.parts
    )


def _is_skipped_path(rel: Path) -> bool:
    if not rel.parts:
        return True
    if rel.parts[0] in {".git", ".mypy_cache", ".pytest_cache", "__pycache__"}:
        return True
    if rel.parts[0] == "patch":
        return True
    return False


def _phase_number(name: str) -> str | None:
    match = re.match(r"PHASE(\d+)", name)
    if not match:
        return None
    return match.group(1)


def _is_report_like(name: str) -> bool:
    return any(
        token in name
        for token in (
            "TEST_REPORT",
            "AUDIT_REPORT",
            "CODE_STYLE_AUDIT",
            "REBUILD_REPORT",
            "REPORT",
        )
    )


def _rewrite_markdown_references(root: Path, replacements: dict[str, str]) -> None:
    if not replacements:
        return

    markdown_files = [
        path
        for path in _markdown_files(root)
        if not _is_skipped_path(path.relative_to(root))
    ]

    by_basename = {
        Path(old).name: new
        for old, new in replacements.items()
    }

    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        updated = text

        for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
            updated = updated.replace(old, _relative_reference(path, root / new, root))
            updated = updated.replace("./" + old, _relative_reference(path, root / new, root))

        for basename, new in by_basename.items():
            updated = re.sub(
                rf"(?<![\w./-]){re.escape(basename)}(?![\w./-])",
                _relative_reference(path, root / new, root),
                updated,
            )

        if updated != text:
            path.write_text(updated, encoding="utf-8")


def _relative_reference(from_file: Path, to_file: Path, root: Path) -> str:
    try:
        return to_file.relative_to(from_file.parent).as_posix()
    except ValueError:
        return _rel(to_file, root)


def _rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan or apply markdown documentation layout.")
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    parser.add_argument("--apply", action="store_true", help="apply planned moves")
    parser.add_argument("--report-file", type=Path, help="write JSON plan report")
    args = parser.parse_args()

    plan = build_markdown_layout_plan(args.root)
    print(render_markdown_layout_plan(plan))

    if args.report_file is not None:
        write_markdown_layout_report(args.report_file, plan)

    if args.apply:
        apply_markdown_layout_plan(plan)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
