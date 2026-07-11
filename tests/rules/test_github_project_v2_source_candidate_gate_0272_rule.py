from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "src/context/github_project_v2_source_candidate_gate_0272.py"
CLI = ROOT / "tools/gate_github_project_v2_source_candidate_0272.py"
README = ROOT / "README.md"
OPERATOR = ROOT / "doc/operator/GITHUB_PROJECT_ACTIONS_CONFIGURATION_0272.md"
GLOBAL = ROOT / "doc/docs/architecture/00_global.dot"
RUNTIME = ROOT / "doc/docs/architecture/runtime/272_github_project_v2_source_candidate_gate.dot"


def test_gate_reuses_existing_decision_contract_and_has_no_network_backend_imports() -> None:
    core = CORE.read_text(encoding="utf-8")
    cli = CLI.read_text(encoding="utf-8")
    assert "SourceCandidateDecision" in core
    assert "apply_source_candidate_decision" in core
    forbidden_imports = (
        "import urllib",
        "from urllib",
        "import requests",
        "from requests",
        "import qdrant_client",
        "from qdrant_client",
        "import psycopg",
        "from psycopg",
        "import sqlite3",
        "import openvino",
        "from openvino",
        "from scheduler",
        "import scheduler",
        "from context.route_proxy",
        "from context.control_proxy",
    )
    for forbidden in forbidden_imports:
        assert forbidden not in core
        assert forbidden not in cli



def test_project_native_mode_does_not_require_actions_bridge() -> None:
    readme = README.read_text(encoding="utf-8")
    operator = OPERATOR.read_text(encoding="utf-8")
    assert "Actions workflow are not\nrequired" in readme
    assert "--check-actions-bridge" in readme
    assert "mode **Project-native**" in operator
    assert "require_actions_deployment = false" in operator
    assert "pont secondaire" in operator


def test_gate_graph_is_connected_to_r6_and_future_r8() -> None:
    global_graph = GLOBAL.read_text(encoding="utf-8")
    runtime_graph = RUNTIME.read_text(encoding="utf-8")
    assert "SourceCandidateGate0272R7" in global_graph
    assert "HandoffBatch0272R6 -> SourceCandidateGate0272R7" in global_graph
    assert "GateRecord0272R7 -> FutureDurable0272R6" in global_graph
    assert "Handoff -> Gate" in runtime_graph
    assert "Record -> Durable" in runtime_graph
