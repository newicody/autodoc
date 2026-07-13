from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "templates/github/scripts/run_autodoc_copilot_advisory.py"


def test_copilot_advisory_uses_jsonl_transport_and_semantic_digest() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    for marker in (
        "extract_advisory",
        '"--output-format=json"',
        '"--stream=off"',
        "semantic_response = canonical(parsed)",
        '"usable_as_authority": False',
    ):
        assert marker in text

    for forbidden in (
        "COPILOT_GITHUB_TOKEN",
        "check=True",
        "process.stderr",
    ):
        assert forbidden not in text
