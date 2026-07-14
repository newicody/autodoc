from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/portable_specialist_real_memory_closure_0284.py"
REPORT = ROOT / "PHASE0284_R6_PORTABLE_SPECIALIST_REAL_MEMORY_CLOSURE_REPORT.md"
ARCHITECTURE = ROOT / "doc/architecture/PORTABLE_SPECIALIST_REAL_MEMORY_CLOSURE_0284.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0284_R6_PORTABLE_SPECIALIST_REAL_MEMORY_CLOSURE.md"


def test_r6_reuses_existing_memory_surfaces() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert "run_portable_specialist_existing_chain_smoke" in source
    assert "build_qdrant_scoped_executor_binding" in source
    assert "inspect_qdrant_scoped_executor_factory" in source
    assert "EXPECTED_E5_DIMENSION = 384" in source
    assert "automatic_cleanup_performed: bool = False" in source


def test_r6_does_not_add_parallel_authority() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert "class LaboratoryManager" not in source
    assert "Scheduler(" not in source
    assert "EventBus(" not in source
    assert "QdrantClient(" not in source
    assert "create_collection" not in source
    assert "delete_collection" not in source
    assert "delete_points" not in source


def test_r6_documents_effect_and_live_path_boundaries() -> None:
    report = REPORT.read_text(encoding="utf-8")
    architecture = ARCHITECTURE.read_text(encoding="utf-8")

    assert "live_path_status: n/a" in report
    assert "live_path_uses_real_backend: n/a" in report
    assert "scheduler_modified: false" in report
    assert "automatic_cleanup_performed: false" in report
    assert "Qdrant returns references only" in architecture
    assert "SQL remains the durable authority" in architecture


def test_r6_manifest_lists_only_phase_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")

    assert "src/context/portable_specialist_real_memory_closure_0284.py" in manifest
    assert "tests/context/test_portable_specialist_real_memory_closure_0284.py" in manifest
    assert "tests/rules/test_portable_specialist_real_memory_closure_0284_rule.py" in manifest
    assert "tools/" not in manifest
