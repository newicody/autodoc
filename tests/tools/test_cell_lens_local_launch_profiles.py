from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from cell_lens_local_launch_profiles import (
    CELL_LENS_LAUNCH_PROFILES_SCHEMA,
    build_cell_lens_launch_profiles,
    detect_qt_platform,
    shell_command,
)


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "cell_lens_local_launch_profiles.py"


def test_detect_qt_platform_prefers_explicit_value() -> None:
    assert detect_qt_platform({"QT_QPA_PLATFORM": "minimal", "WAYLAND_DISPLAY": "wayland-1"}) == "minimal"


def test_detect_qt_platform_prefers_wayland_before_xcb() -> None:
    assert detect_qt_platform({"WAYLAND_DISPLAY": "wayland-1", "DISPLAY": ":0"}) == "wayland"


def test_detect_qt_platform_uses_xcb_when_only_display_exists() -> None:
    assert detect_qt_platform({"DISPLAY": ":0"}) == "xcb"


def test_build_cell_lens_launch_profiles_returns_three_profiles() -> None:
    bundle = build_cell_lens_launch_profiles(Path(".var/cell_lens_demo/cells.jsonl"), qt_platform="wayland")

    assert bundle.schema == CELL_LENS_LAUNCH_PROFILES_SCHEMA
    assert [profile.name for profile in bundle.profiles] == ["vispy-desktop", "browser-canvas", "sse-stream"]
    assert bundle.profiles[0].environment == (
        ("PYTHONPATH", "src:."),
        ("VISPY_APP", "pyqt6"),
        ("QT_QPA_PLATFORM", "wayland"),
    )
    assert bundle.profiles[1].url == "http://127.0.0.1:8766/view.html"
    assert bundle.profiles[2].url == "http://127.0.0.1:8765/cells.sse"


def test_shell_command_formats_environment_prefix() -> None:
    profile = build_cell_lens_launch_profiles(Path("cells.jsonl"), qt_platform="wayland").profiles[0]

    command = shell_command(profile)

    assert command.startswith("PYTHONPATH=src:. VISPY_APP=pyqt6 QT_QPA_PLATFORM=wayland ")
    assert "tools/visualize_cell_population_vispy.py" in command


def test_cell_lens_local_launch_profiles_cli_outputs_json(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--journal",
            str(tmp_path / "cells.jsonl"),
            "--qt-platform",
            "wayland",
        ],
        cwd=ROOT,
        env={"PYTHONPATH": "src:.:tools"},
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["schema"] == "missipy.cell_lens_local_launch_profiles.v1"
    assert len(payload["profiles"]) == 3
    assert payload["profiles"][0]["environment"]["QT_QPA_PLATFORM"] == "wayland"


def test_cell_lens_local_launch_profiles_cli_outputs_shell_commands(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--journal",
            str(tmp_path / "cells.jsonl"),
            "--qt-platform",
            "wayland",
            "--shell",
        ],
        cwd=ROOT,
        env={"PYTHONPATH": "src:.:tools"},
        text=True,
        capture_output=True,
        check=True,
    )

    assert "QT_QPA_PLATFORM=wayland" in completed.stdout
    assert "http://127.0.0.1:8766/view.html" in completed.stdout
