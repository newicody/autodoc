from __future__ import annotations

import subprocess


def _tracked(pattern: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", pattern],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_generated_svg_are_not_versioned() -> None:
    assert _tracked("*.svg") == []


def test_optimized_python_bytecode_is_not_versioned() -> None:
    assert _tracked("*.pyo") == []


def test_patchqueue_local_config_is_not_versioned() -> None:
    assert _tracked(".patchqueue.local.json") == []
