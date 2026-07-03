#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from context.cell_snapshot_journal_reader import (
    read_cell_snapshot_jsonl,
    tail_cell_snapshot_jsonl,
)
from visualization.cell_lens_projection import (
    CellRenderPoint,
    latest_snapshot_by_cell,
    project_cell_snapshots,
)


STATUS_COLORS = {
    "healthy": (0.20, 0.85, 0.35, 1.0),
    "late": (0.95, 0.75, 0.20, 1.0),
    "degraded": (0.95, 0.35, 0.20, 1.0),
    "stale": (0.55, 0.20, 0.85, 1.0),
    "terminal": (0.45, 0.45, 0.45, 1.0),
}


def render_points_to_arrays(points: tuple[CellRenderPoint, ...]) -> tuple[list[tuple[float, float]], list[float], list[tuple[float, float, float, float]]]:
    positions = [(point.x, point.y) for point in points]
    sizes = [point.size for point in points]
    colors = [STATUS_COLORS.get(point.status, STATUS_COLORS["degraded"]) for point in points]
    return positions, sizes, colors


def load_initial_points(journal: Path, *, limit: int | None = None) -> tuple[dict[str, Any], int]:
    result = read_cell_snapshot_jsonl(journal, limit=limit)
    latest = latest_snapshot_by_cell(result.snapshots)
    return latest, journal.stat().st_size if journal.exists() else 0


def run_vispy_viewer(journal: Path, *, tail: bool, interval_seconds: float, limit: int | None) -> int:
    try:
        from vispy import app, scene
    except ImportError as exc:
        raise SystemExit(
            "VisPy is required for the desktop viewer. Install it in the active environment before running this tool."
        ) from exc

    latest, offset = load_initial_points(journal, limit=limit)

    canvas = scene.SceneCanvas(keys="interactive", title="MissiPy Cell Lens", size=(1000, 800), show=True)
    view = canvas.central_widget.add_view()
    view.camera = "panzoom"
    markers = scene.visuals.Markers(parent=view.scene)

    def redraw() -> None:
        points = project_cell_snapshots(latest.values(), latest_only=False)
        positions, sizes, colors = render_points_to_arrays(points)
        markers.set_data(positions, face_color=colors, edge_color=None, size=sizes)
        canvas.update()

    def poll_tail(event: object | None = None) -> None:
        nonlocal offset
        if not tail:
            return
        result = tail_cell_snapshot_jsonl(journal, offset=offset, max_lines=2048)
        offset = result.next_offset
        for snapshot in result.snapshots:
            latest[snapshot.cell_id] = snapshot
        redraw()

    redraw()

    timer = None
    if tail:
        timer = app.Timer(interval=interval_seconds, connect=poll_tail, start=True)

    try:
        app.run()
    finally:
        if timer is not None:
            timer.stop()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a missipy.cell.v1 JSONL journal with VisPy.")
    parser.add_argument("--journal", required=True, help="Input JSONL cell snapshot journal.")
    parser.add_argument("--tail", action="store_true", help="Follow the journal with non-blocking tail reads.")
    parser.add_argument("--interval-seconds", type=float, default=0.25)
    parser.add_argument("--limit", type=int, default=None, help="Optional replay limit before tailing.")
    args = parser.parse_args()

    if args.interval_seconds <= 0:
        raise SystemExit("--interval-seconds must be > 0")

    return run_vispy_viewer(
        Path(args.journal),
        tail=args.tail,
        interval_seconds=args.interval_seconds,
        limit=args.limit,
    )


if __name__ == "__main__":
    raise SystemExit(main())
