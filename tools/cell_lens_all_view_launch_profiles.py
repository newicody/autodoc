#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path


CELL_LENS_ALL_VIEW_LAUNCH_PROFILES_SCHEMA = "missipy.cell_lens_all_view_launch_profiles.v1"


@dataclass(frozen=True, slots=True)
class CellLensAllViewLaunchProfile:
    name: str
    purpose: str
    command: tuple[str, ...]
    environment: tuple[tuple[str, str], ...] = ()
    url: str = ""
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "command": list(self.command),
            "environment": {key: value for key, value in self.environment},
            "name": self.name,
            "notes": list(self.notes),
            "purpose": self.purpose,
            "url": self.url,
        }


@dataclass(frozen=True, slots=True)
class CellLensAllViewLaunchProfileBundle:
    journal_path: str
    profiles: tuple[CellLensAllViewLaunchProfile, ...]
    schema: str = CELL_LENS_ALL_VIEW_LAUNCH_PROFILES_SCHEMA

    def to_json_dict(self) -> dict[str, object]:
        return {
            "journal_path": self.journal_path,
            "profiles": [profile.to_json_dict() for profile in self.profiles],
            "schema": self.schema,
        }


def detect_qt_platform(env: dict[str, str] | None = None) -> str:
    values = env if env is not None else os.environ
    if values.get("QT_QPA_PLATFORM"):
        return values["QT_QPA_PLATFORM"]
    if values.get("WAYLAND_DISPLAY"):
        return "wayland"
    if values.get("DISPLAY"):
        return "xcb"
    return "offscreen"


def build_cell_lens_all_view_launch_profiles(
    journal: Path,
    *,
    browser_port: int = 8766,
    health_port: int = 8767,
    sse_port: int = 8765,
    qt_platform: str | None = None,
) -> CellLensAllViewLaunchProfileBundle:
    if browser_port <= 0:
        raise ValueError("browser_port must be > 0")
    if health_port <= 0:
        raise ValueError("health_port must be > 0")
    if sse_port <= 0:
        raise ValueError("sse_port must be > 0")

    platform = qt_platform or detect_qt_platform()
    journal_text = str(journal)

    profiles = (
        CellLensAllViewLaunchProfile(
            name="vispy-desktop",
            purpose="Open the desktop Cell Lens viewer from the cell journal.",
            command=(
                "python",
                "tools/visualize_cell_population_vispy.py",
                "--journal",
                journal_text,
                "--tail",
                "--interval-seconds",
                "0.25",
            ),
            environment=(
                ("PYTHONPATH", "src:."),
                ("VISPY_APP", "pyqt6"),
                ("QT_QPA_PLATFORM", platform),
            ),
            notes=(
                "Use wayland on a native Wayland session.",
                "Use xcb only when the Qt XCB platform plugin dependencies are present.",
                "Set MISSIPY_CELL_LENS_JOURNAL to this same journal path on the kernel process.",
            ),
        ),
        CellLensAllViewLaunchProfile(
            name="browser-canvas",
            purpose="Serve the local read-only browser Canvas view.",
            command=(
                "python",
                "tools/cell_snapshot_browser_view_server.py",
                "--journal",
                journal_text,
                "--port",
                str(browser_port),
            ),
            environment=(("PYTHONPATH", "src:."),),
            url=f"http://127.0.0.1:{browser_port}/view.html",
            notes=("The server stays running until interrupted.",),
        ),
        CellLensAllViewLaunchProfile(
            name="browser-health-canvas",
            purpose="Serve the local read-only browser Canvas health view.",
            command=(
                "python",
                "tools/cell_snapshot_browser_health_view_server.py",
                "--journal",
                journal_text,
                "--port",
                str(health_port),
            ),
            environment=(("PYTHONPATH", "src:."),),
            url=f"http://127.0.0.1:{health_port}/health-view.html",
            notes=("Shows status counts and a health legend.", "The server stays running until interrupted."),
        ),
        CellLensAllViewLaunchProfile(
            name="sse-stream",
            purpose="Serve the local read-only SSE stream.",
            command=("python", "tools/cell_snapshot_sse_server.py", "--journal", journal_text, "--port", str(sse_port)),
            environment=(("PYTHONPATH", "src:."),),
            url=f"http://127.0.0.1:{sse_port}/cells.sse",
            notes=("Useful for curl and EventSource checks.",),
        ),
    )

    return CellLensAllViewLaunchProfileBundle(journal_path=journal_text, profiles=profiles)


def shell_command(profile: CellLensAllViewLaunchProfile) -> str:
    env_prefix = " ".join(f"{key}={value}" for key, value in profile.environment)
    command = " ".join(profile.command)
    return f"{env_prefix} {command}".strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Print all local read-only Cell Lens launch profiles.")
    parser.add_argument("--journal", default=".var/cell_lens_demo/cells.jsonl")
    parser.add_argument("--browser-port", type=int, default=8766)
    parser.add_argument("--health-port", type=int, default=8767)
    parser.add_argument("--sse-port", type=int, default=8765)
    parser.add_argument("--qt-platform", default="")
    parser.add_argument("--shell", action="store_true", help="Print shell commands instead of JSON.")
    args = parser.parse_args()

    bundle = build_cell_lens_all_view_launch_profiles(
        Path(args.journal),
        browser_port=args.browser_port,
        health_port=args.health_port,
        sse_port=args.sse_port,
        qt_platform=args.qt_platform or None,
    )

    if args.shell:
        for profile in bundle.profiles:
            print(f"# {profile.name}: {profile.purpose}")
            print(shell_command(profile))
            if profile.url:
                print(f"# url: {profile.url}")
            print()
        return 0

    print(json.dumps(bundle.to_json_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
