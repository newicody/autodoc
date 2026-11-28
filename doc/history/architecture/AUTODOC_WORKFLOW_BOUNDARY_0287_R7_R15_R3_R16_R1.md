# Autodoc workflow boundary

## Repository responsibilities

### `newicody/projects`

- receives Issues and ProjectV2 changes;
- executes the controlled-research GitHub Action;
- produces authoritative, advisory and manifest artifacts;
- receives controlled result publication.

### `newicody/autodoc`

- versions the Projects installation template;
- fetches artifacts from `newicody/projects`;
- validates correlation and digests;
- persists the durable intake;
- executes the Scheduler, laboratories and specialists;
- projects and recalls through OpenVINO/Qdrant;
- publishes only through an explicit controlled boundary.

## Root Actions rule

```text
newicody/autodoc/.github/workflows/*.yml   forbidden
newicody/autodoc/.github/workflows/*.yaml  forbidden
```

The directory may contain documentation such as `README.md`.
