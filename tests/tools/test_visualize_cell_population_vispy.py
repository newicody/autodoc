from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from visualize_cell_population_vispy import render_points_to_arrays  # noqa: E402
from visualization.cell_lens_projection import CellRenderPoint  # noqa: E402


def test_render_points_to_arrays_is_renderer_neutral_until_vispy_runtime() -> None:
    points = (
        CellRenderPoint(
            cell_id="cell-1",
            source_class="llm.answer",
            lifecycle_state="running",
            x=0.1,
            y=0.2,
            z=0.0,
            size=8.0,
            health_score=1.0,
            status="healthy",
            age=1.0,
            cost=2.0,
        ),
    )

    positions, sizes, colors = render_points_to_arrays(points)

    assert positions == [(0.1, 0.2)]
    assert sizes == [8.0]
    assert colors[0][-1] == 1.0
