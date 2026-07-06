#!/usr/bin/env python3
"""OpenVINO/E5 live smoke runner that reuses the existing embedding CLI.

0138 deliberately does not introduce a new adapter.  It verifies that the
repository has the existing inference membrane and, when --execute is passed,
runs the existing tools/embed_e5.py entrypoint with a query and a passage.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import sys
from typing import Sequence

DEFAULT_MODEL_DIR = "/home/eric/model/openvino/multilingual-e5-small"
DEFAULT_QUERY = "query: route proxy scheduler vector indexing smoke"
DEFAULT_PASSAGE = "passage: Scheduler queues vector indexing work while OpenVINO stays behind the existing inference membrane."


@dataclass(frozen=True, slots=True)
class OpenVINOE5SmokeSurface:
    key: str
    path: Path
    reason: str

    def to_mapping(self, *, root: Path) -> dict[str, str]:
        return {
            "key": self.key,
            "status": "present" if self.path.exists() else "missing",
            "path": _display_path(self.path, root=root),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class OpenVINOE5SmokeCommand:
    role: str
    text: str
    argv: tuple[str, ...]

    def shell_preview(self) -> str:
        return " ".join(_shell_quote(part) for part in self.argv)


@dataclass(frozen=True, slots=True)
class OpenVINOE5SmokePlan:
    repository_root: Path
    model_dir: Path
    execute: bool
    surfaces: tuple[OpenVINOE5SmokeSurface, ...]
    commands: tuple[OpenVINOE5SmokeCommand, ...]

    @property
    def ready(self) -> bool:
        return all(surface.path.exists() for surface in self.surfaces)

    def missing_surfaces(self) -> tuple[OpenVINOE5SmokeSurface, ...]:
        return tuple(surface for surface in self.surfaces if not surface.path.exists())

    def to_markdown(self) -> str:
        lines = [
            "# OpenVINO/E5 live smoke plan",
            "",
            f"repository_root: `{self.repository_root}`",
            f"model_dir: `{self.model_dir}`",
            f"ready_for_openvino_e5_smoke: `{str(self.ready).lower()}`",
            f"execute: `{str(self.execute).lower()}`",
            "",
            "## Existing surfaces",
            "",
            "| key | status | path | reason |",
            "| --- | --- | --- | --- |",
        ]
        for surface in self.surfaces:
            row = surface.to_mapping(root=self.repository_root)
            lines.append(f"| {row['key']} | {row['status']} | `{row['path']}` | {row['reason']} |")
        lines.extend(["", "## Commands", ""])
        for command in self.commands:
            lines.append(f"### {command.role}")
            lines.append("")
            lines.append("```bash")
            lines.append(command.shell_preview())
            lines.append("```")
            lines.append("")
        lines.extend([
            "## Boundary",
            "",
            "- reuses tools/embed_e5.py as existing operator CLI when present",
            "- reuses src/inference/openvino_embedding_adapter.py as existing membrane",
            "- reuses src/inference/openvino_runtime.py as real OpenVINO import boundary",
            "- does not import OpenVINO from Scheduler, RouteProxy, Qdrant, or context contracts",
            "- dry-run is the default; --execute is required for backend execution",
        ])
        return "\n".join(lines) + "\n"


def build_openvino_e5_smoke_plan(
    root: Path,
    *,
    model_dir: Path,
    query_text: str,
    passage_text: str,
    execute: bool,
) -> OpenVINOE5SmokePlan:
    root = root.resolve()
    model_dir = model_dir.expanduser()
    embed_cli = root / "tools" / "embed_e5.py"
    surfaces = (
        OpenVINOE5SmokeSurface(
            key="embed_e5_cli",
            path=embed_cli,
            reason="existing E5/OpenVINO operator CLI",
        ),
        OpenVINOE5SmokeSurface(
            key="openvino_embedding_membrane",
            path=root / "src" / "inference" / "openvino_embedding_adapter.py",
            reason="existing OpenVINO/E5 embedding membrane",
        ),
        OpenVINOE5SmokeSurface(
            key="openvino_runtime_boundary",
            path=root / "src" / "inference" / "openvino_runtime.py",
            reason="single real OpenVINO import boundary",
        ),
    )
    commands = (
        OpenVINOE5SmokeCommand(
            role="query",
            text=query_text,
            argv=(sys.executable, str(embed_cli), "--model-dir", str(model_dir), _ensure_prefix(query_text, "query: ")),
        ),
        OpenVINOE5SmokeCommand(
            role="passage",
            text=passage_text,
            argv=(sys.executable, str(embed_cli), "--model-dir", str(model_dir), _ensure_prefix(passage_text, "passage: ")),
        ),
    )
    return OpenVINOE5SmokePlan(
        repository_root=root,
        model_dir=model_dir,
        execute=execute,
        surfaces=surfaces,
        commands=commands,
    )


def run_commands(plan: OpenVINOE5SmokePlan) -> int:
    if not plan.ready:
        for surface in plan.missing_surfaces():
            print(f"missing surface: {surface.key} -> {surface.path}", file=sys.stderr)
        return 2
    failures = 0
    for command in plan.commands:
        print(f"==> {command.role}")
        completed = subprocess.run(
            command.argv,
            cwd=plan.repository_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        if completed.returncode != 0:
            failures += 1
    return 1 if failures else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan or run OpenVINO/E5 smoke through existing repo surfaces.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root")
    parser.add_argument("--model-dir", default=os.environ.get("AUTODOC_E5_MODEL_DIR", DEFAULT_MODEL_DIR))
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--passage", default=DEFAULT_PASSAGE)
    parser.add_argument("--format", choices=("markdown", "shell"), default="markdown")
    parser.add_argument("--execute", action="store_true", help="Run existing tools/embed_e5.py commands")
    args = parser.parse_args(argv)

    plan = build_openvino_e5_smoke_plan(
        Path(args.root),
        model_dir=Path(args.model_dir),
        query_text=args.query,
        passage_text=args.passage,
        execute=bool(args.execute),
    )
    if args.format == "markdown":
        print(plan.to_markdown(), end="")
    else:
        for command in plan.commands:
            print(command.shell_preview())

    if args.execute:
        return run_commands(plan)
    return 0 if plan.ready else 2


def _ensure_prefix(value: str, prefix: str) -> str:
    return value if value.startswith(prefix) else prefix + value


def _display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _shell_quote(value: str) -> str:
    if not value:
        return "''"
    safe = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+-=./:@")
    if all(ch in safe for ch in value):
        return value
    return "'" + value.replace("'", "'\\''") + "'"


if __name__ == "__main__":
    raise SystemExit(main())
