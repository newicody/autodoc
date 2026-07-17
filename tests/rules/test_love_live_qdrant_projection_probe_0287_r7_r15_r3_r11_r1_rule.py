from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "src/context/love_live_qdrant_projection_probe_0287.py"
EXECUTOR = ROOT / "src/inference/qdrant_client_projection_executor.py"
TOOL = ROOT / "tools/probe_love_live_qdrant_projection_0287.py"


def test_r11_r1_reuses_existing_live_ports_and_keeps_sql_authority() -> None:
    service = SERVICE.read_text(encoding="utf-8")
    executor = EXECUTOR.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")
    for required in (
        "inspect_love_live_projection_probe",
        "execute_love_live_projection_probe",
        "await projector.project",
        "authority_store.put_projection",
        "authority_store.get_object",
        "authority_store.get_projection",
        "qdrant_vectors_serialized",
        "authoritative_body_serialized",
        "confirm_plan_digest",
    ):
        assert required in service
    for required in (
        "def read_named_reference_point",
        "self._client.retrieve",
        "with_payload=True",
        "with_vectors=False",
        "self._gate.allow_search",
        "QdrantClientReferencePoint",
    ):
        assert required in executor
    for required in (
        "open_love_postgresql_authority",
        "build_multilingual_e5_small_pipeline",
        "build_qdrant_client_projection_executor",
        "LoveQdrantLiveAnalysisProjection",
        "AUTODOC_QDRANT_POINT_WRITE_ALLOWED",
    ):
        assert required in tool
    combined = service + executor + tool
    for forbidden in (
        "Scheduler(",
        "LaboratoryManager",
        "create_collection(",
        "delete_collection(",
        "update_collection_aliases(",
        "with_vectors=True",
    ):
        assert forbidden not in combined
