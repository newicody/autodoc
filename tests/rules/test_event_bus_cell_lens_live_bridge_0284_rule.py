from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "src/context/event_bus_cell_lens_live_bridge_0284.py"
MAIN = ROOT / "src/main.py"
PROFILE = ROOT / "tools/cell_lens_all_view_launch_profiles.py"
ARCHITECTURE = ROOT / "doc/architecture/EVENTBUS_VISPY_LIVE_BRIDGE_0284.md"
DOT = ROOT / "doc/architecture/EVENTBUS_VISPY_LIVE_BRIDGE_0284.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0284_R1_R1_EVENTBUS_VISPY_LIVE_BRIDGE.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0284_R1_R1_EVENTBUS_VISPY_LIVE_BRIDGE.md"
REPORT = ROOT / "PHASE0284_R1_R1_EVENTBUS_VISPY_LIVE_BRIDGE_REPORT.md"


def test_bridge_reuses_observation_contract_and_has_no_control_path() -> None:
    source = BRIDGE.read_text(encoding="utf-8")
    for required in (
        "EventBusSubscriber",
        "subscribe(None)",
        "CellObservationEvent",
        "CellSnapshotJournalWriter",
        "asyncio.to_thread",
        "specialist_ref",
        "laboratory_ref",
        "sql_ref",
        "qdrant_ref",
    ):
        assert required in source
    for forbidden in (
        "Scheduler(",
        ".emit(",
        ".publish(",
        "PolicyEngine(",
        "PriorityQueue(",
        "sqlite3",
        "qdrant_client",
        "openvino",
        "requests.",
        "httpx.",
        "urlopen(",
    ):
        assert forbidden not in source


def test_activation_is_optional_and_composed_outside_kernel_launcher() -> None:
    source = MAIN.read_text(encoding="utf-8")
    launcher = (ROOT / "src/kernel/launcher.py").read_text(encoding="utf-8")

    assert "MISSIPY_CELL_LENS_JOURNAL" in source
    assert "EventBusCellLensLiveBridge(launcher.event_bus" in source
    assert "event_bus_cell_lens_live_bridge_0284" not in launcher


def test_existing_vispy_profile_uses_existing_tail_mode() -> None:
    source = PROFILE.read_text(encoding="utf-8")
    assert '"--tail"' in source
    assert '"--interval-seconds"' in source
    assert '"0.25"' in source
    assert "MISSIPY_CELL_LENS_JOURNAL" in source


def test_phase_documents_lock_passive_boundaries() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, DOT, MANIFEST, CHANGELOG, REPORT)
    )
    for required in (
        "architecture_preserved: true",
        "existing_eventbus_reused: true",
        "existing_cell_contract_reused: true",
        "existing_journal_reused: true",
        "existing_vispy_tail_reused: true",
        "new_bus_added: false",
        "new_scheduler_added: false",
        "scheduler_modified: false",
        "eventbus_observation_only: true",
        "external_dependencies_added: false",
    ):
        assert required in combined


def test_report_uses_allowed_review_values_and_preserves_next_functional_patch() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: green",
        "live_path_uses_real_backend: true",
        "context_contract_version: missipy.cell.v1",
        "context_contract_changed: false",
        "search_commands_bounded: n/a",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "0284-r2-portable-specialist-contract",
    ):
        assert required in report


def test_phase_adds_dot_source_but_no_generated_svg() -> None:
    assert DOT.exists()
    assert not any(ROOT.rglob("EVENTBUS_VISPY_LIVE_BRIDGE_0284.svg"))
