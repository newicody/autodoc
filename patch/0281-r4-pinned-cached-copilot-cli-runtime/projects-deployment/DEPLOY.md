# Deploy 0281-r4 to newicody/projects

```text
projects_repository_change_required: true
```

```bash
cd /home/eric/projet/git/projects

git apply --check \
  /home/eric/projet/git/autodoc/patch/0281-r4-pinned-cached-copilot-cli-runtime/projects-deployment/projects.patch.diff

git apply \
  /home/eric/projet/git/autodoc/patch/0281-r4-pinned-cached-copilot-cli-runtime/projects-deployment/projects.patch.diff

git diff --check
git add .github/workflows/autodoc-controlled-research.yml
git commit -m "Cache pinned Copilot CLI runtime"
git push origin master
```

Then update the selected-actions policy:

```bash
gh api \
  --method PUT \
  repos/newicody/projects/actions/permissions/selected-actions \
  --input \
  /home/eric/projet/git/autodoc/patch/0281-r4-pinned-cached-copilot-cli-runtime/projects-deployment/selected-actions-policy.json
```

Verify:

```bash
gh api repos/newicody/projects/actions/permissions/selected-actions
```
