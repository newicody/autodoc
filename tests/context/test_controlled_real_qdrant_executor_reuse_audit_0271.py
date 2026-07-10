from context.controlled_real_qdrant_executor_reuse_audit_0271 import (
    REQUIRED_SURFACES,
    audit_controlled_real_qdrant_executor_reuse,
)


def _baseline_sources() -> dict[str, str]:
    return {
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
        REQUIRED_SURFACES[3]: 'BOUNDARY = {"calls_qdrant_api": False, "upserts_qdrant_points": False}',
        REQUIRED_SURFACES[4]: 'BOUNDARY = {"calls_qdrant_api": False, "writes_qdrant_points": False}',
        REQUIRED_SURFACES[5]: "audit only",
        REQUIRED_SURFACES[6]: "plan only",
        REQUIRED_SURFACES[7]: "acceptance only",
        REQUIRED_SURFACES[8]: 'parser.add_argument("--demo-qdrant")',
    }


def test_0271_audit_proves_protocol_exists_but_live_executor_is_missing() -> None:
    result = audit_controlled_real_qdrant_executor_reuse(_baseline_sources())

    assert result.valid is True
    assert result.protocol_found is True
    assert result.projection_demo_found is True
    assert result.recall_demo_found is True
    assert result.live_executor_found is False
    assert result.implementation_needed is True
    assert result.new_executor_module_justified is True
    assert result.network_used is False
    assert result.qdrant_called is False
    assert result.runtime_manager_created is False


def test_0271_audit_detects_existing_live_executor_for_reuse() -> None:
    sources = _baseline_sources()
    sources["src/inference/existing_live_executor.py"] = """
class ExistingLiveExecutor:
    def upsert_points(self): ...
    def search_vector(self): ...
"""

    result = audit_controlled_real_qdrant_executor_reuse(sources)

    assert result.valid is True
    assert result.live_executor_found is True
    assert result.implementation_needed is False
    assert result.new_executor_module_justified is False
    assert result.live_executor_paths == ("src/inference/existing_live_executor.py",)
