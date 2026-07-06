#!/usr/bin/env python3
"""Local vector indexing live-smoke chain through existing operator surfaces.

0141 intentionally does not create a new OpenVINO adapter, Qdrant adapter,
Scheduler runner, or RouteProxy worker.  It composes the already validated
operator surfaces:

* tools/run_openvino_e5_live_smoke.py for OpenVINO/E5 backend execution
* tools/run_qdrant_projection_live_smoke.py for Qdrant REST projection smoke

The default execution mode proves the local chain can run in one operator
command.  A strict full-vector handoff can be requested with
``--strict-vector-handoff``; in that mode the tool requires a machine-readable
384-dimensional vector file because the existing ``tools/embed_e5.py`` operator
currently reports previews for humans.  That keeps the boundary honest: no
parallel embedding implementation is invented just to extract vectors.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any, Sequence

DEFAULT_MODEL_DIR = "/home/eric/model/openvino/multilingual-e5-small"
DEFAULT_QDRANT_URL = "http://127.0.0.1:6333"
DEFAULT_COLLECTION = "autodoc_smoke_e5_384"
DEFAULT_DIMENSION = 384
DEFAULT_SQL_REF = "sql:smoke/vector-indexing/0141"
DEFAULT_TEXT = "passage: Local vector indexing smoke runs OpenVINO E5 then Qdrant projection while SQL remains authority."


@dataclass(frozen=True, slots=True)
class LocalVectorSmokeSurface:
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
class LocalVectorSmokeCommand:
    role: str
    argv: tuple[str, ...]

    def shell_preview(self) -> str:
        return " ".join(_shell_quote(part) for part in self.argv)


@dataclass(frozen=True, slots=True)
class MachineVectorProbe:
    available: bool
    source: str
    reason: str
    dimension: int | None = None
    l2_norm: float | None = None

    def to_markdown_line(self) -> str:
        if self.available:
            return f"machine_vector_available: `true` source: `{self.source}` dimension: `{self.dimension}` l2_norm: `{self.l2_norm:.8f}`"
        return f"machine_vector_available: `false` source: `{self.source}` reason: `{self.reason}`"


@dataclass(frozen=True, slots=True)
class LocalVectorIndexingSmokePlan:
    repository_root: Path
    model_dir: Path
    qdrant_url: str
    collection: str
    dimension: int
    sql_ref: str
    text: str
    execute: bool
    strict_vector_handoff: bool
    vector_json: Path | None
    surfaces: tuple[LocalVectorSmokeSurface, ...]
    commands: tuple[LocalVectorSmokeCommand, ...]
    machine_vector_probe: MachineVectorProbe

    @property
    def ready(self) -> bool:
        return all(surface.path.exists() for surface in self.surfaces)

    def missing_surfaces(self) -> tuple[LocalVectorSmokeSurface, ...]:
        return tuple(surface for surface in self.surfaces if not surface.path.exists())

    @property
    def ready_for_strict_vector_handoff(self) -> bool:
        return self.ready and self.machine_vector_probe.available

    def to_markdown(self) -> str:
        lines = [
            "# Local vector indexing live smoke plan",
            "",
            f"repository_root: `{self.repository_root}`",
            f"model_dir: `{self.model_dir}`",
            f"qdrant_url: `{self.qdrant_url}`",
            f"collection: `{self.collection}`",
            f"dimension: `{self.dimension}`",
            f"sql_ref: `{self.sql_ref}`",
            f"ready_for_local_vector_indexing_smoke: `{str(self.ready).lower()}`",
            f"strict_vector_handoff: `{str(self.strict_vector_handoff).lower()}`",
            f"ready_for_strict_vector_handoff: `{str(self.ready_for_strict_vector_handoff).lower()}`",
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
        lines.extend([
            "",
            "## Machine vector handoff",
            "",
            self.machine_vector_probe.to_markdown_line(),
            "",
            "## Commands",
            "",
        ])
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
            "- reuses tools/run_openvino_e5_live_smoke.py for OpenVINO/E5 execution",
            "- reuses tools/run_qdrant_projection_live_smoke.py for Qdrant projection",
            "- reuses src/inference/openvino_embedding_adapter.py as the embedding membrane",
            "- reuses src/inference/qdrant_projection_adapter.py as the projection membrane",
            "- does not create LocalVectorIndexingOrchestrator",
            "- does not create VectorOpenVINOEmbeddingAdapter",
            "- does not create VectorQdrantProjectionAdapter",
            "- Scheduler remains outside OpenVINO and Qdrant",
            "- RouteProxy remains outside OpenVINO and Qdrant",
            "- SQLContextStore remains durable authority; Qdrant stores projection/recall only",
            "- strict full-vector handoff requires machine-readable vector output instead of parsing human previews",
        ])
        return "\n".join(lines) + "\n"


def build_local_vector_indexing_smoke_plan(
    root: Path,
    *,
    model_dir: Path,
    qdrant_url: str,
    collection: str,
    dimension: int,
    sql_ref: str,
    text: str,
    execute: bool,
    strict_vector_handoff: bool,
    vector_json: Path | None,
) -> LocalVectorIndexingSmokePlan:
    root = root.resolve()
    model_dir = model_dir.expanduser()
    vector_json = vector_json.expanduser() if vector_json is not None else None
    text = _ensure_prefix(text, "passage: ")
    surfaces = (
        LocalVectorSmokeSurface(
            key="openvino_live_smoke_tool",
            path=root / "tools" / "run_openvino_e5_live_smoke.py",
            reason="existing OpenVINO/E5 operator smoke tool",
        ),
        LocalVectorSmokeSurface(
            key="qdrant_projection_smoke_tool",
            path=root / "tools" / "run_qdrant_projection_live_smoke.py",
            reason="existing Qdrant operator smoke tool",
        ),
        LocalVectorSmokeSurface(
            key="embed_e5_cli",
            path=root / "tools" / "embed_e5.py",
            reason="existing E5/OpenVINO CLI used by 0138",
        ),
        LocalVectorSmokeSurface(
            key="openvino_embedding_membrane",
            path=root / "src" / "inference" / "openvino_embedding_adapter.py",
            reason="existing embedding membrane",
        ),
        LocalVectorSmokeSurface(
            key="openvino_runtime_boundary",
            path=root / "src" / "inference" / "openvino_runtime.py",
            reason="single real OpenVINO import boundary",
        ),
        LocalVectorSmokeSurface(
            key="qdrant_projection_adapter",
            path=root / "src" / "inference" / "qdrant_projection_adapter.py",
            reason="existing Qdrant projection membrane",
        ),
        LocalVectorSmokeSurface(
            key="vector_indexing_job_plan",
            path=root / "src" / "context" / "vector_indexing_job_plan.py",
            reason="existing vector indexing job contract",
        ),
        LocalVectorSmokeSurface(
            key="sql_context_store",
            path=root / "src" / "context" / "sql_context_store.py",
            reason="durable context authority",
        ),
    )
    machine_vector_probe = inspect_machine_vector_source(vector_json, expected_dimension=dimension)
    commands = (
        LocalVectorSmokeCommand(
            role="openvino_e5_live_smoke",
            argv=(
                sys.executable,
                str(root / "tools" / "run_openvino_e5_live_smoke.py"),
                str(root),
                "--model-dir",
                str(model_dir),
                "--passage",
                text,
                "--execute",
            ),
        ),
        LocalVectorSmokeCommand(
            role="qdrant_projection_live_smoke",
            argv=(
                sys.executable,
                str(root / "tools" / "run_qdrant_projection_live_smoke.py"),
                str(root),
                "--qdrant-url",
                qdrant_url,
                "--collection",
                collection,
                "--dimension",
                str(dimension),
                "--sql-ref",
                sql_ref,
                "--execute",
            ),
        ),
    )
    return LocalVectorIndexingSmokePlan(
        repository_root=root,
        model_dir=model_dir,
        qdrant_url=qdrant_url,
        collection=collection,
        dimension=dimension,
        sql_ref=sql_ref,
        text=text,
        execute=execute,
        strict_vector_handoff=strict_vector_handoff,
        vector_json=vector_json,
        surfaces=surfaces,
        commands=commands,
        machine_vector_probe=machine_vector_probe,
    )


def inspect_machine_vector_source(vector_json: Path | None, *, expected_dimension: int) -> MachineVectorProbe:
    if vector_json is None:
        return MachineVectorProbe(
            available=False,
            source="none",
            reason="no --vector-json file provided; existing embed_e5.py currently exposes human previews, not a full machine vector handoff",
        )
    if not vector_json.exists():
        return MachineVectorProbe(
            available=False,
            source=str(vector_json),
            reason="vector json file does not exist",
        )
    try:
        vector = load_vector_json(vector_json)
        validate_vector(vector, expected_dimension=expected_dimension)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return MachineVectorProbe(available=False, source=str(vector_json), reason=str(exc))
    norm = math.sqrt(sum(value * value for value in vector))
    return MachineVectorProbe(
        available=True,
        source=str(vector_json),
        reason="machine-readable vector accepted",
        dimension=len(vector),
        l2_norm=norm,
    )


def load_vector_json(path: Path) -> tuple[float, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("vector") or payload.get("values")
    if not isinstance(payload, list):
        raise ValueError("vector json must be a list or an object with vector/values")
    return tuple(float(value) for value in payload)


def validate_vector(vector: Sequence[float], *, expected_dimension: int) -> None:
    if len(vector) != expected_dimension:
        raise ValueError(f"vector dimension must be {expected_dimension}, got {len(vector)}")
    norm = math.sqrt(sum(value * value for value in vector))
    if not math.isfinite(norm) or norm <= 0:
        raise ValueError("vector norm must be finite and > 0")


def run_local_vector_indexing_smoke(plan: LocalVectorIndexingSmokePlan) -> int:
    if not plan.ready:
        for surface in plan.missing_surfaces():
            print(f"missing surface: {surface.key} -> {surface.path}", file=sys.stderr)
        return 2
    if plan.strict_vector_handoff and not plan.machine_vector_probe.available:
        print(
            "strict vector handoff requested but no machine-readable vector is available; "
            "next step should extend tools/embed_e5.py or the existing OpenVINO membrane to emit full vectors",
            file=sys.stderr,
        )
        return 4

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
    if failures:
        return 1

    print("# Local vector indexing live smoke result")
    print("")
    print("openvino_e5_smoke: `ok`")
    print("qdrant_projection_smoke: `ok`")
    print(f"strict_vector_handoff: `{str(plan.strict_vector_handoff).lower()}`")
    print(f"machine_vector_available: `{str(plan.machine_vector_probe.available).lower()}`")
    print("boundary: `existing OpenVINO smoke tool + existing Qdrant smoke tool`")
    if not plan.machine_vector_probe.available:
        print("note: `0141 validates the live operator chain; full vector handoff needs machine-readable E5 output`")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan or run local vector indexing smoke through existing operator surfaces.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR)
    parser.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--dimension", type=int, default=DEFAULT_DIMENSION)
    parser.add_argument("--sql-ref", default=DEFAULT_SQL_REF)
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--vector-json", type=Path, default=None, help="Optional machine-readable vector file for strict handoff validation")
    parser.add_argument("--strict-vector-handoff", action="store_true", help="Fail unless --vector-json supplies a validated full vector")
    parser.add_argument("--format", choices=("markdown", "shell"), default="markdown")
    parser.add_argument("--execute", action="store_true", help="Run both existing live smoke tools")
    args = parser.parse_args(argv)

    plan = build_local_vector_indexing_smoke_plan(
        Path(args.root),
        model_dir=Path(args.model_dir),
        qdrant_url=args.qdrant_url,
        collection=args.collection,
        dimension=args.dimension,
        sql_ref=args.sql_ref,
        text=args.text,
        execute=bool(args.execute),
        strict_vector_handoff=bool(args.strict_vector_handoff),
        vector_json=args.vector_json,
    )
    if args.format == "markdown":
        print(plan.to_markdown(), end="")
    else:
        for command in plan.commands:
            print(command.shell_preview())
    if args.execute:
        return run_local_vector_indexing_smoke(plan)
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
