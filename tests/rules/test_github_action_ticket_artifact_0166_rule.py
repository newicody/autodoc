from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "src" / "context" / "github_action_ticket_artifact.py"
TOOL = ROOT / "tools" / "build_github_action_ticket_artifact_from_event.py"
WORKFLOW = ROOT / "templates" / "github" / "autodoc-ticket-artifact.yml"
SCRIPT = ROOT / "templates" / "github" / "scripts" / "build_autodoc_ticket_artifact.py"
ISSUE_FORM = ROOT / "templates" / "github" / "ISSUE_TEMPLATE" / "autodoc_task.yml"
DOC = ROOT / "doc" / "architecture" / "GITHUB_ACTION_TICKET_ARTIFACT_0166.md"
RULE = ROOT / "doc" / "code-rules" / "0166_github_action_ticket_artifact_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0166_CHANGED_FILES.md"


def test_0166_files_exist() -> None:
    for path in [CONTRACT, TOOL, WORKFLOW, SCRIPT, ISSUE_FORM, DOC, RULE, MANIFEST]:
        assert path.exists()


def test_0166_contract_reuses_project_push_frame_and_has_no_network() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    for token in ["ProjectPushFrame", "ProjectPushContextOptions", "CopilotPreliminaryOpinionArtifact", "validate_copilot_preliminary_opinion", "ticket, column name", "advisory only"]:
        assert token in text
    for forbidden in ["requests.", "urllib.", "http.client", "subprocess", "DbApiSqlContextStore(", "Qdrant", "OpenVINO", "fcrontab", "rc-service", "rc-update"]:
        assert forbidden not in text


def test_0166_tool_uses_event_file_only() -> None:
    text = TOOL.read_text(encoding="utf-8")
    for token in ["GITHUB_EVENT_PATH", "build_github_action_ticket_artifact", "build_copilot_preliminary_opinion_for_ticket_artifact", "no GitHub API call", "no remote mutation"]:
        assert token in text
    for forbidden in ["requests.", "urllib.", "http.client", "rc-service", "rc-update", "fcrontab", "DbApiSqlContextStore(", "Qdrant", "OpenVINO"]:
        assert forbidden not in text


def test_0166_templates_define_external_action_and_issue_form() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")
    issue_form = ISSUE_FORM.read_text(encoding="utf-8")
    for token in ["issues:", "actions/upload-artifact@v4", "autodoc-ticket-artifact-${{ github.run_id }}", "autodoc-copilot-preliminary-opinion-${{ github.run_id }}"]:
        assert token in workflow
    for token in ["Standalone external-repository ticket artifact builder", "no GitHub API call", "missipy.github_action.ticket_artifact.v1", "usable_as_authority"]:
        assert token in script
    for token in ["Colonne workflow", "include_total_project", "include_repository_context", "requested_depth"]:
        assert token in issue_form


def test_0166_docs_lock_boundaries() -> None:
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    for token in ["ticket + column name + options", "Copilot preliminary opinion is advisory only", "external idea repository", "does not read GitHub API", "artifact sibling", "reuse 0165 ProjectPushFrame"]:
        assert token in doc
    for token in ["Do not create a new scheduler", "Do not call GitHub API", "Reuse 0165 ProjectPushFrame", "Copilot preliminary opinion is advisory only", "Ticket artifact carries only ticket + column name + options"]:
        assert token in rule


def test_0166_manifest_lists_limited_changes() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    for path in ["src/context/github_action_ticket_artifact.py", "tools/build_github_action_ticket_artifact_from_event.py", "templates/github/autodoc-ticket-artifact.yml", "templates/github/scripts/build_autodoc_ticket_artifact.py", "templates/github/ISSUE_TEMPLATE/autodoc_task.yml", "tests/context/test_github_action_ticket_artifact_0166.py", "tests/tools/test_build_github_action_ticket_artifact_from_event_0166.py", "tests/rules/test_github_action_ticket_artifact_0166_rule.py", "doc/architecture/GITHUB_ACTION_TICKET_ARTIFACT_0166.md", "doc/code-rules/0166_github_action_ticket_artifact_rule.md", "doc/docs/architecture/runtime/166_github_action_ticket_artifact.dot", "doc/CHANGELOG_0166_GITHUB_ACTION_TICKET_ARTIFACT.md", "doc/manifests/MANIFEST_0166_CHANGED_FILES.md", "PHASE0166_TEST_REPORT.md"]:
        assert path in text
