# Manifest 0281-r6 — controlled advisory Issue publication

Changed files:

- `src/context/github_controlled_advisory_issue_publication_0281.py`
- `tools/publish_github_advisory_issue_comment_0281.py`
- `tests/context/test_github_controlled_advisory_issue_publication_0281.py`
- `tests/tools/test_publish_github_advisory_issue_comment_0281.py`
- `tests/rules/test_github_controlled_advisory_issue_publication_0281_rule.py`
- `doc/architecture/GITHUB_CONTROLLED_ADVISORY_ISSUE_PUBLICATION_0281.md`
- `doc/manifests/MANIFEST_0281_R6_CONTROLLED_ADVISORY_ISSUE_PUBLICATION.md`
- `PHASE0281_R6_CONTROLLED_ADVISORY_ISSUE_PUBLICATION_REPORT.md`

Repository impact:

```text
autodoc: change required
projects: no Git-tracked change required
projects_repository_change_required: false
```

The Issue comment mutation is executed locally only after explicit operator
approval and exact plan digest confirmation.
