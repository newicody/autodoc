from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "CONTROLFS_MANIFEST_SCHEMA.md"
MODULE = ROOT / "src" / "runtime" / "controlfs_manifest.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_controlfs_manifest_schema_document_locks_priority_1_scope() -> None:
    text = _read(DOC)

    required_phrases = [
        "missipy.controlfs.route_manifest.v1",
        "/run/autodoc/controlfs/desired/routes/<route_id>/manifest.json",
        "Scheduler writes desired/routes/<route_id>/manifest.json.",
        "RouteProxy reads desired/ and writes active/status.",
        "Workers never write desired/ or active/.",
        "It does not add:",
        "real ControlFS daemon",
        "real RouteProxy",
        "real shm",
        "semaphores",
        "NetworkBridge",
        "HardwareBridge",
        "Scheduler refactor",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_controlfs_manifest_module_is_parser_only() -> None:
    text = _read(MODULE)

    required_phrases = [
        "It only parses and validates route manifests",
        "create shared memory",
        "create semaphores",
        "start a RouteProxy daemon",
        "change Scheduler behavior",
        "mutate ControlFS directories",
    ]

    for phrase in required_phrases:
        assert phrase in text
