from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = ROOT / "templates" / "github" / "scripts"


def test_all_github_template_python_scripts_compile() -> None:
    scripts = tuple(sorted(SCRIPTS_ROOT.rglob("*.py")))
    assert scripts, f"no Python scripts found below {SCRIPTS_ROOT}"

    failures: list[str] = []
    for path in scripts:
        relative = path.relative_to(ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        try:
            compile(source, relative, "exec")
        except SyntaxError as exc:
            line = exc.lineno or 0
            column = exc.offset or 0
            failures.append(
                f"{relative}:{line}:{column}: {exc.msg}"
            )

    assert not failures, (
        "GitHub template Python syntax failures:\n"
        + "\n".join(failures)
    )
