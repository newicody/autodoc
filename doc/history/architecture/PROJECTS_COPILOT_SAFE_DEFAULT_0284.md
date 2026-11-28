# Projects Copilot safe default — 0284-r1-r5

## Decision

The Projects workflow already keeps the authoritative request independent
from the optional Copilot advisory. Installation must preserve that
boundary from the first dispatch.

```text
initial_copilot_enabled: false
authoritative_request_always_built: true
advisory_required: false
github_token_ephemeral: true
durable_copilot_secret_required: false
operator_activation_required: true
```

## Existing workflow reused

The current workflow already provides:

```text
copilot-requests: write
GITHUB_TOKEN: ${{ github.token }}
AUTODOC_COPILOT_REQUIRED: "false"
pinned Copilot CLI and cache
manifest valid without advisory artifact
```

This patch changes no executable workflow. It aligns only the cumulative
installation procedure and locks that alignment with a source rule.

## Boundary

```text
authoritative request -> always produced
Copilot advisory      -> disabled at installation
                        -> explicitly enabled after validation
                        -> optional and non-authoritative
dual manifest         -> always produced
```

```text
scheduler_modified: false
github_api_added: false
projects_runtime_changed: false
projects_installation_changed: true
external_dependencies_added: false
```
