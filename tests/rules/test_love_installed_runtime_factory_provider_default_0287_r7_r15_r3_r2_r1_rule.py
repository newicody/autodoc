from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/love_installed_runtime_factory_0287.py"
EXAMPLE = ROOT / "config/love_installed_runtime.example.ini"


def test_example_preserves_blank_legacy_marker_and_documents_default() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    example = EXAMPLE.read_text(encoding="utf-8")
    provider = (
        "context.love_manual_installed_runtime_provider_0287:"
        "build_installed_runtime_ports"
    )

    assert "factory =\n" in example
    assert provider in example
    assert "DEFAULT_INSTALLED_RUNTIME_PROVIDER" in source
    assert "or DEFAULT_INSTALLED_RUNTIME_PROVIDER" in source
    assert "factory = " + provider not in example
