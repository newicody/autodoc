from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from inference.qdrant_client_projection_executor import QdrantClientDependencyReadiness


def _load_tool():
    path = Path(__file__).resolve().parents[2] / "tools/check_qdrant_client_projection_executor_0271.py"
    spec = importlib.util.spec_from_file_location("check_qdrant_client_projection_executor_0271", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_writes_read_only_dependency_report(monkeypatch, tmp_path, capsys) -> None:
    module = _load_tool()
    output = tmp_path / "readiness.json"
    monkeypatch.setattr(
        module,
        "inspect_qdrant_client_dependency",
        lambda: QdrantClientDependencyReadiness(installed=True, version="1.18.0"),
    )
    monkeypatch.setattr(
        module,
        "parse_args",
        lambda: type("Args", (), {"output": str(output), "format": "summary"})(),
    )

    assert module.main() == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["network_used"] is False
    assert payload["qdrant_called"] is False
    assert "touches_shm=False" in capsys.readouterr().out
