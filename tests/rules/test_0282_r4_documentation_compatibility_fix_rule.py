from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAYERS = ROOT / "doc/ARCHITECTURE_LAYERS.md"
CURRENT = ROOT / "doc/architecture/CURRENT_ARCHITECTURE_STATE_0154.md"
GRAPH = ROOT / "doc/docs/architecture/runtime/174_rebuilt_runtime_global_current_state.dot"
REPORT = ROOT / "PHASE0282_R4_R1_DOCUMENTATION_COMPATIBILITY_FIX_REPORT.md"


def test_0270_anchors_and_0282_current_state_coexist() -> None:
    layers = LAYERS.read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")
    assert "Current operational baseline — 0270" in layers
    assert "Current operational baseline — 0282-r4" in layers
    assert "canonical index refreshed by 0270" in current
    assert "canonical index refreshed by 0282-r4" in current
    assert "historical compatibility" in layers
    assert "Compatibility anchor" in current


def test_0174_contract_tokens_and_0282_topology_coexist() -> None:
    graph = GRAPH.read_text(encoding="utf-8")
    for token in (
        "0174 rebuilt runtime global current-state draft",
        "External workflow / exchange",
        "Configured server dataset",
        "Scheduler authority",
        "Local compute / context",
        "Observation / visualization",
        "forbidden command path",
        "forbidden direct writer",
        "forbidden internal bus source",
        "0282-r4 current operational architecture",
        "ProjectV2 cycle-history development",
        "ProjectV2 append-only cycle history",
        "existing-Scheduler fake laboratory",
    ):
        assert token in graph


def test_fix_is_documentation_only_and_does_not_revert_r4() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for required in (
        "runtime_source_modified: false",
        "architecture_topology_reverted: false",
        "new_runtime_module_added: false",
        "new_cli_added: false",
        "new_adapter_added: false",
        "github_mutation_performed: false",
        "scheduler_modified: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in report
