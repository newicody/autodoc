# Projects bundle managed synchronization

```text
Autodoc template tree
        |
        +--> projects_bundle_manifest.json
        |
        +--> active managed files
        |
        v
read-only drift audit
        |
        +--> identical
        +--> copy candidates
        +--> safe delete candidates (retired only)
        +--> unknown extras (review only)
        |
        v
operator-reviewed rsync without --delete
        |
        v
newicody/projects
```

The manifest governs ownership, not remote deployment. It performs no GitHub
API call and no mutation.

Unknown files inside `.github/ISSUE_TEMPLATE`, `.github/workflows` or `scripts`
remain project-owned until an operator explicitly classifies them.
