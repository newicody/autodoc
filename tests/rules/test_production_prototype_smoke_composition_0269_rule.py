from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "src/context/production_prototype_smoke_composition_0269.py"
TOOL = ROOT / "tools/run_production_prototype_smoke_composition_0269.py"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0269_PRODUCTION_PROTOTYPE_SMOKE_COMPOSITION_CHANGED_FILES.md"
RULE = ROOT / "doc/code-rules/0269_production_prototype_smoke_composition_rule.md"


def test_core_is_stdlib_typed_and_effect_free() -> None:
    text = CORE.read_text(encoding="utf-8")
    assert "@dataclass(frozen=True, slots=True)" in text
    assert "subprocess" not in text
    assert "argparse" not in text
    assert "RuntimeManager" not in text
    assert "Scheduler.run" not in text
    assert "import openvino" not in text.lower()
    assert "from openvino" not in text.lower()
    assert "qdrant_client" not in text


def test_cli_only_executes_existing_python_phase_tools() -> None:
    text = TOOL.read_text(encoding="utf-8")
    assert "subprocess.run" in text
    assert "rc-service" not in text
    assert "rc-update" not in text
    assert "service start" not in text
    assert "api.github.com" not in text.lower()
    assert "requests." not in text
    assert "PyGithub" not in text


def test_rule_and_manifest_lock_the_phase_boundary() -> None:
    rule = RULE.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "0260 -> 0261 -> 0262 -> 0263 -> 0264 -> 0265 -> 0266 -> 0267 -> 0268" in rule
    assert "new RuntimeManager" in rule
    assert "Scheduler.run is not modified" in rule
    assert "no non-stdlib dependency" in rule
    assert "src/context/production_prototype_smoke_composition_0269.py" in manifest
    assert "tools/run_production_prototype_smoke_composition_0269.py" in manifest
