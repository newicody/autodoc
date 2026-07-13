from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GRAPH = (
    ROOT
    / "doc/docs/architecture/runtime/"
    "174_rebuilt_runtime_global_current_state.dot"
)
REPORT = (
    ROOT
    / "PHASE0282_R4_R2_OBSERVATION_TOKEN_COMPATIBILITY_FIX_REPORT.md"
)


def test_observation_cluster_preserves_both_exact_contract_tokens() -> None:
    graph = GRAPH.read_text(encoding="utf-8")
    assert "Observation / visualization" in graph
    assert "Observation only" in graph
    assert 'label="Observation / visualization\\nObservation only"' in graph


def test_fix_is_label_only_and_keeps_locked_boundaries() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for required in (
        "runtime_source_modified: false",
        "architecture_topology_modified: false",
        "graph_label_compatibility_only: true",
        "new_runtime_module_added: false",
        "new_cli_added: false",
        "new_adapter_added: false",
        "github_mutation_performed: false",
        "scheduler_modified: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in report
