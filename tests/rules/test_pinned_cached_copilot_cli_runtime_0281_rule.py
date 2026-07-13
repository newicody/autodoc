from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = (
    ROOT / "templates/github/autodoc-dual-artifact.yml",
    ROOT
    / "templates/github/projects-repository/.github/workflows"
    / "autodoc-controlled-research.yml",
)


def test_copilot_cli_is_pinned_cached_and_not_globally_reinstalled() -> None:
    for path in WORKFLOWS:
        text = path.read_text(encoding="utf-8")
        for required in (
            'AUTODOC_COPILOT_CLI_VERSION: "1.0.70"',
            "AUTODOC_COPILOT_CLI_PREFIX:",
            "uses: actions/cache@v4",
            "id: autodoc-copilot-cli-cache",
            "steps.autodoc-copilot-cli-cache.outputs.cache-hit != 'true'",
            '"@github/copilot@$AUTODOC_COPILOT_CLI_VERSION"',
            "--prefix",
            "--no-audit",
            "--no-fund",
            "--omit=dev",
            'COPILOT_AUTO_UPDATE: "false"',
            "AUTODOC_COPILOT_COMMAND:",
            "/node_modules/.bin/copilot",
            "actual_version",
        ):
            assert required in text
        for forbidden in (
            "npm install --global @github/copilot",
            "npm install -g @github/copilot",
            "@github/copilot@latest",
            "@github/copilot@prerelease",
            "restore-keys:",
        ):
            assert forbidden not in text


def test_cache_key_is_exactly_scoped_by_platform_and_version() -> None:
    for path in WORKFLOWS:
        text = path.read_text(encoding="utf-8")
        assert "autodoc-copilot-cli-v1-${{ runner.os }}" in text
        assert "${{ runner.arch }}" in text
        assert "env.AUTODOC_COPILOT_CLI_VERSION" in text


def test_projects_change_is_explicitly_declared() -> None:
    report = (
        ROOT
        / "PHASE0281_R4_PINNED_CACHED_COPILOT_CLI_RUNTIME_REPORT.md"
    ).read_text(encoding="utf-8")
    assert "projects_repository_change_required: true" in report
    assert "actions/cache@v4" in report
    assert "newicody/projects" in report
