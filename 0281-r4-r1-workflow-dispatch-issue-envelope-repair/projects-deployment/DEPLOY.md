# Deploy 0281-r4-r1-workflow-dispatch-issue-envelope-repair to newicody/projects

The private `projects` workflow may differ from the public Autodoc template.

First try:

```bash
cd /home/eric/projet/git/projects

git apply --check \
  /home/eric/projet/git/autodoc/patch/0281-r4-r1-workflow-dispatch-issue-envelope-repair/projects-deployment/projects.patch.diff
```

If it applies:

```bash
git apply \
  /home/eric/projet/git/autodoc/patch/0281-r4-r1-workflow-dispatch-issue-envelope-repair/projects-deployment/projects.patch.diff
```

If it does not apply, replace only the deployed workflow with the canonical
target included in this bundle:

```bash
cp \
  /home/eric/projet/git/autodoc/patch/0281-r4-r1-workflow-dispatch-issue-envelope-repair/projects-deployment/.github/workflows/autodoc-controlled-research.yml \
  .github/workflows/autodoc-controlled-research.yml
```

Then:

```bash
git diff --check
git diff -- .github/workflows/autodoc-controlled-research.yml
git add .github/workflows/autodoc-controlled-research.yml
git commit -m "Repair workflow dispatch Issue envelope"
git push origin master
```
