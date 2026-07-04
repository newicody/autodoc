from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "BABY_FORK_RUNTIME_PROJECTION_COMPATIBILITY.md"
MODULE = ROOT / "src" / "context" / "baby_fork_runtime_projection.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_projection_compatibility_doc_mentions_real_variant_count_issue() -> None:
    text = _read(DOC)

    required_phrases = [
        '"variant_count": 0',
        "variant_generator.generated_variants",
        "variant_generator_stub.variants",
        "final_context.variants",
        "variant_count",
        "variant_ids",
        "sha256:projection",
        "deterministic SHA-256",
        "real shared memory",
        "RouteProxy daemon",
        "Scheduler wiring",
        "ControlFS mutation",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_projection_module_uses_hashlib_and_variant_fallbacks() -> None:
    text = _read(MODULE)

    required_phrases = [
        "import hashlib",
        "def _stable_sha256",
        "def _find_first_variant_list",
        "generated_variants",
        "variant_generator_stub",
        "variant_ids",
    ]

    for phrase in required_phrases:
        assert phrase in text
