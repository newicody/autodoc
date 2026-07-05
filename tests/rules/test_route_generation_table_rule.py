from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "runtime" / "route_generation_table.py"
DOC = ROOT / "doc" / "architecture" / "ROUTE_GENERATION_TABLE_0091_R2.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0091_R2_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0091_R2_TEST_REPORT.md"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_0091_r2_generation_table_locks_operational_intent() -> None:
    text = _read(MODULE) + "\n" + _read(DOC)
    required = [
        "route_id -> current_generation",
        "incremented only when a new route generation is materialized",
        "g2/g3",
        "No CLI",
        "No OpenRC service and no resident daemon",
        "No watcher",
        "No Scheduler.run() modification",
        "No live mmap resize",
        "ControlProxy does not decide security",
        "Scheduler/policy/zone remain the authority",
        "Not /dev/shm-only",
    ]
    for phrase in required:
        assert phrase in text


def test_0091_r2_manifest_keeps_scope_small() -> None:
    manifest = _read(MANIFEST)
    required = [
        "src/runtime/route_generation_table.py",
        "tests/runtime/test_route_generation_table.py",
        "tests/rules/test_route_generation_table_rule.py",
        "doc/architecture/ROUTE_GENERATION_TABLE_0091_R2.md",
        "PHASE0091_R2_TEST_REPORT.md",
    ]
    for phrase in required:
        assert phrase in manifest
    forbidden = [
        "src/kernel/scheduler.py",
        "src/kernel/queue.py",
        "src/kernel/dispatcher.py",
        "tools/",
        "OpenRC",
        "/dev/shm mandatory",
    ]
    for phrase in forbidden:
        assert phrase not in manifest


def test_0091_r2_report_contains_code_rule_alignment_block() -> None:
    report = _read(REPORT)
    required = [
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: green",
        "live_path_uses_real_backend: false",
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "search_commands_bounded: n/a",
    ]
    for phrase in required:
        assert phrase in report
