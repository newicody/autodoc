from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_OWNER = _ROOT / "src/context/love_tool_bounded_scheduler_owner_0287.py"
_TOOL = _ROOT / "tools/run_github_research_love_closed_loop_0287.py"
_DISPATCH = _ROOT / "src/context/github_research_scheduler_dispatch_0287.py"
_RULE = (
    _ROOT
    / "doc/code-rules/0287_r16_r42_tool_bounded_scheduler_ownership_rule.md"
)


def test_owner_reuses_injected_scheduler_without_parallel_infrastructure() -> None:
    source = _OWNER.read_text(encoding="utf-8")

    for forbidden in (
        "Scheduler(",
        "Dispatcher(",
        "EventBus(",
        "PriorityQueue(",
        "threading",
        "multiprocessing",
        "subprocess",
    ):
        assert forbidden not in source

    assert "asyncio.create_task(scheduler.run()" in source
    assert "await scheduler.shutdown()" in source
    assert "await run_task" in source


def test_operational_closed_loop_imports_the_scheduler_owned_adapter() -> None:
    source = _TOOL.read_text(encoding="utf-8")

    assert "love_tool_bounded_scheduler_owner_0287" in source
    assert "prepare_github_research_love_closed_loop," in source


def test_dispatch_remains_fail_closed_and_does_not_start_scheduler() -> None:
    source = _DISPATCH.read_text(encoding="utf-8")

    assert "the existing Scheduler must already be running; " in source
    assert "r16-r9 will not start a second Scheduler" in source
    assert "await scheduler.run()" not in source
    assert "create_task(scheduler.run()" not in source


def test_code_rule_records_exact_scheduler_ownership_boundary() -> None:
    rule = _RULE.read_text(encoding="utf-8")

    assert "même Scheduler injecté" in rule
    assert "aucun second Scheduler" in rule
    assert "externally-managed" in rule
    assert "finally" in rule
