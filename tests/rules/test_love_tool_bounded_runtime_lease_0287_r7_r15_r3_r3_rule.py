from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "src/context/love_imported_actions_runtime_contract_0287.py"
TOOL = ROOT / "tools/run_love_actions_closed_loop_0287.py"


def test_runtime_lease_is_a_process_local_effect_boundary() -> None:
    source = CONTRACT.read_text(encoding="utf-8")
    for marker in (
        "ImportedActionsRuntimeLease",
        "runtime lease is process-local",
        "for hook in reversed(self.close_hooks)",
        "to_readback_mapping",
        'owner_ref="runtime-owner:legacy-direct-ports"',
        "only a tool-bounded runtime may own close hooks",
    ):
        assert marker in source
    for forbidden in (
        "from kernel.launcher import Launcher",
        "Scheduler(",
        "psycopg.connect(",
        "QdrantClient(",
        "RealOpenVINORuntime(",
    ):
        assert forbidden not in source


def test_preview_tool_closes_only_tool_bounded_owned_resources() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for marker in (
        "acquire_imported_actions_runtime_lease",
        "runtime_lease=runtime_lease",
        'output["_r15_runtime_lease"]',
        "_close_tool_bounded_runtime_lease",
        'runtime.scheduler_lifecycle == "tool-bounded"',
    ):
        assert marker in source
    assert "await runtime.scheduler.shutdown()" in source
