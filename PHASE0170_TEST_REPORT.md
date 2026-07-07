# Phase 0170 test report

Planned validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/context/test_github_issue_attachment_manifest_0170.py \
  tests/tools/test_build_github_issue_attachment_manifest_0170.py \
  tests/tools/test_github_idea_repo_attachment_bootstrap_bundle_0170.py \
  tests/rules/test_github_issue_attachment_manifest_0170_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

Boundary: reference-only attachment manifest, no GitHub API call, no remote mutation, no user artifacts in Autodoc repository.
