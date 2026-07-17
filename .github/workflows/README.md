# No active Autodoc repository workflows

`newicody/autodoc` does not execute the controlled-research artifact producer.

The maintained workflow source belongs to the installation bundle for
`newicody/projects`:

```text
templates/github/projects-repository/.github/workflows/
  autodoc-controlled-research.yml
```

The operational direction is:

```text
newicody/projects Actions artifacts
→ local Autodoc fetch/import
→ PostgreSQL intake and operator decision
→ Scheduler/laboratory execution
→ controlled publication back to ProjectV2
```

Do not add `.yml` or `.yaml` files to this directory.
