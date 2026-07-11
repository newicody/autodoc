from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/project_github_project_v2_source_candidate_vector_0272.py"


def test_tool_help_exposes_controlled_effect_arguments() -> None:
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "--durable-report" in completed.stdout
    assert "--execute" in completed.stdout
    assert "--policy-decision-id" in completed.stdout
    assert "--qdrant-url" in completed.stdout
    assert "--collection" in completed.stdout
