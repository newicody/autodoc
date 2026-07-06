from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_architecture_docs_and_surfaces.py"


def test_0153_tool_exists() -> None:
    assert TOOL.exists()


def test_0153_json_output_contains_expected_sections() -> None:
    result = subprocess.run(
        [sys.executable, str(TOOL), str(ROOT), "--format", "json"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    assert payload["schema"] == "missipy.architecture_docs_surface_audit.v1"
    assert "surface_audits" in payload
    assert "docs_audit" in payload
    assert "sql_context_store_ast" in payload
    keys = {item["key"] for item in payload["surface_audits"]}
    assert "openvino_e5_embedding" in keys
    assert "qdrant_projection" in keys
    assert "sql_context_store_persistence" in keys


def test_0153_markdown_output_mentions_roles() -> None:
    result = subprocess.run(
        [sys.executable, str(TOOL), str(ROOT), "--format", "markdown"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    text = result.stdout
    assert "Architecture docs and surface audit" in text
    assert "Surface completeness" in text
    assert "Documentation inventory" in text
    assert "SQL store AST inventory" in text


def test_0153_execute_writes_reports(tmp_path: Path) -> None:
    out = tmp_path / "audit"
    subprocess.run(
        [sys.executable, str(TOOL), str(ROOT), "--output-dir", str(out), "--execute"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert (out / "architecture_docs_surface_audit.json").exists()
    assert (out / "architecture_docs_surface_audit_report.md").exists()


def test_0153_surface_rollup_is_bounded() -> None:
    result = subprocess.run(
        [sys.executable, str(TOOL), str(ROOT), "--format", "json"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    for value in payload["phase_rollup"].values():
        assert 0 <= value <= 100
