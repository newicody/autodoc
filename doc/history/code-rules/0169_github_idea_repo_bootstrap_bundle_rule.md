# 0169 code rule — GitHub idea repository bootstrap bundle

0169 may only prepare local bootstrap files for the external idea repository.

Required boundaries:

- reuse 0166 templates
- target the external idea repository
- no GitHub API call
- no remote mutation
- GitHub Actions artifacts remain the source system
- no user artifacts in Autodoc repository
- no server dataset write
- no conversion or inference
- no SQL/qdrant write

`--write` is allowed only for an explicit local `--external-repo-root`. It must
copy files locally and must not call `git push`, `gh api`, `workflow_dispatch`,
`urllib.request`, or `requests`.

If a generated patch differs from the manually corrected source, the tracked
source and Git commit take precedence over the patch trace.
