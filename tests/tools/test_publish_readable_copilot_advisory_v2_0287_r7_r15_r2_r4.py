from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/publish_readable_copilot_advisory_v2_0287.py"


def _load():
    spec = spec_from_file_location("publish_readable_copilot_test", TOOL)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_cli_is_preview_first_and_requires_combined_digest_for_execute() -> None:
    tool = _load()
    args = tool._parser().parse_args(
        [
            "--preview", "p.json",
            "--artifact-identity", "i.json",
            "--repository", "newicody/projects",
            "--issue-number", "1",
            "--policy-decision-id", "policy:test",
            "--operator-decision", "approve",
            "--updated-date", "2026-07-17",
        ]
    )
    assert args.execute is False
    assert args.confirm_plan_digest == ""


def test_dynamic_loader_registers_module_before_execution(tmp_path: Path) -> None:
    tool = _load()
    module_path = tmp_path / "loaded.py"
    module_path.write_text("VALUE = 7\n", encoding="utf-8")
    loaded = tool._load_module(module_path, "readable_dynamic_load_test")
    assert loaded.VALUE == 7
    assert sys.modules["readable_dynamic_load_test"] is loaded
