from pathlib import Path

from tools.cell_lens_all_view_launch_profiles import (
    build_cell_lens_all_view_launch_profiles,
)


def test_vispy_profile_tails_the_same_optional_kernel_journal() -> None:
    journal = Path(".var/cell_lens_live/cells.jsonl")
    bundle = build_cell_lens_all_view_launch_profiles(
        journal,
        qt_platform="offscreen",
    )
    profile = next(item for item in bundle.profiles if item.name == "vispy-desktop")

    assert profile.command == (
        "python",
        "tools/visualize_cell_population_vispy.py",
        "--journal",
        str(journal),
        "--tail",
        "--interval-seconds",
        "0.25",
    )
    assert any("MISSIPY_CELL_LENS_JOURNAL" in note for note in profile.notes)
