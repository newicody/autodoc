import json
from pathlib import Path

from context.controlled_real_qdrant_executor_reuse_audit_0271 import REQUIRED_SURFACES
from tools.audit_controlled_real_qdrant_executor_reuse_0271 import main


def test_0271_cli_writes_audit_report(tmp_path: Path, capsys) -> None:
    contents = {
        REQUIRED_SURFACES[0]: """
from typing import Protocol
class QdrantProjectionExecutor(Protocol):
    def upsert_points(self): ...
    def search_vector(self): ...
def build_qdrant_projection_batch(): ...
def unique_sql_context_refs_from_recall(): ...
""",
        REQUIRED_SURFACES[1]: """
class DemoQdrantProjectionExecutor:
    def upsert_points(self): ...
    def search_vector(self): ...
""",
        REQUIRED_SURFACES[2]: """
class DemoQdrantRecallExecutor:
    def upsert_points(self): ...
    def search_vector(self): ...
""",
        REQUIRED_SURFACES[3]: '{"calls_qdrant_api": False, "upserts_qdrant_points": False}',
        REQUIRED_SURFACES[4]: '{"calls_qdrant_api": False, "writes_qdrant_points": False}',
        REQUIRED_SURFACES[5]: "audit",
        REQUIRED_SURFACES[6]: "plan",
        REQUIRED_SURFACES[7]: "accept",
        REQUIRED_SURFACES[8]: "--demo-qdrant",
    }
    for relative, text in contents.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    output = tmp_path / "report.json"
    code = main([
        "--repo-root", str(tmp_path),
        "--output", str(output),
        "--format", "summary",
    ])

    assert code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["live_executor_found"] is False
    assert payload["next_recommended_patch"].startswith("0271-r2-")
    assert "audit_valid=True" in capsys.readouterr().out
