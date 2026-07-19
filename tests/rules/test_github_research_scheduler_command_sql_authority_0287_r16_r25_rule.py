from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/github_research_scheduler_command_sql_authority_0287.py"
BINDING = ROOT / "src/context/love_postgresql_authority_binding_0287.py"
ARCH = ROOT / "doc/architecture/GITHUB_RESEARCH_SCHEDULER_COMMAND_SQL_AUTHORITY_0287.md"
RULE = (
    ROOT
    / "doc/code-rules/rules"
    / "github_research_scheduler_command_sql_authority_0287_r16_r25.md"
)
README = ROOT / "templates/github/projects-repository/README_INSTALLATION.md"


def test_r16_r25_locks_relational_typed_command_authority() -> None:
    module = MODULE.read_text(encoding="utf-8")
    binding = BINDING.read_text(encoding="utf-8")
    architecture = ARCH.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")

    for token in [
        "class DbApiGitHubResearchSchedulerCommandStore",
        "scheduler_command_authorizations",
        "scheduler_command_github_correlations",
        "scheduler_command_context_refs",
        "scheduler_command_evidence_refs",
        '"pending"',
    ]:
        assert token in module

    ddl = module[module.index("statements = (") : module.index("def put_command")]
    assert "payload_json" not in ddl
    assert "metadata_json" not in ddl
    assert " JSON" not in ddl.upper()

    assert "scheduler_command_store.initialize_schema()" in binding
    assert '"scheduler_command_json_storage_used": False' in binding
    assert "Aucune de ces tables ne contient de colonne JSON" in architecture
    assert "Réserver JSON aux frontières GitHub" in rule
    assert "Persistance PostgreSQL relationnelle — r16-r25" in readme
