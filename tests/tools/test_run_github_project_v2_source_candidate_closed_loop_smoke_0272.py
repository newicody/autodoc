from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_github_project_v2_source_candidate_closed_loop_smoke_0272.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("projectv2_closed_loop_tool_0272", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_args_keeps_real_effects_explicit() -> None:
    tool = _load_tool()
    args = tool.parse_args(
        (
            "--gate-record",
            "gate.json",
            "--db-path",
            "state.sqlite3",
            "--collection",
            "candidate_vectors",
            "--qdrant-url",
            "http://127.0.0.1:6333",
            "--recall-limit",
            "5",
            "--execute",
            "--policy-decision-id",
            "policy:0272:r10:cli",
        )
    )
    assert args.gate_record == Path("gate.json")
    assert args.db_path == Path("state.sqlite3")
    assert args.collection == "candidate_vectors"
    assert args.recall_limit == 5
    assert args.execute is True
    assert args.policy_decision_id == "policy:0272:r10:cli"


def test_cli_binds_one_qdrant_executor_with_write_and_search() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "build_db_api_sql_context_store_binding_report" in source
    assert "build_qdrant_client_projection_executor" in source
    assert "allow_write=True" in source
    assert "allow_search=True" in source
    assert "wait_for_write=True" in source
