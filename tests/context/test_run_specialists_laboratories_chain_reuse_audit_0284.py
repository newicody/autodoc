from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = (
    ROOT
    / "tools/"
    "run_specialists_laboratories_chain_reuse_audit_0284.py"
)


def _load_tool():
    spec = importlib.util.spec_from_file_location(
        "run_specialists_laboratories_chain_reuse_audit_0284",
        TOOL,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tool_reports_missing_surfaces_without_importing_them(
    tmp_path,
):
    tool = _load_tool()
    payload = tool.run_audit(tmp_path)

    assert payload["valid"] is False
    assert payload["audited_module_imported"] is False
    assert payload["network_used"] is False


def test_atomic_writer(tmp_path):
    tool = _load_tool()
    output = tmp_path / "reports" / "audit.json"
    payload = {"valid": True, "issues": []}

    tool._write_json_atomic(output, payload)

    assert json.loads(
        output.read_text(encoding="utf-8")
    ) == payload
    assert not output.with_suffix(".json.tmp").exists()
