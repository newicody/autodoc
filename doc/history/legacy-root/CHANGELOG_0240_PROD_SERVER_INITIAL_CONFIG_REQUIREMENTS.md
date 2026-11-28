# Changelog 0240 - production server initial configuration requirements

## r2

Replaces the previous wording with initial production server configuration
requirements.

Adds the GitHub artifact-exchange surface already developed in earlier phases:

```text
GITHUB_TOKEN environment variable
repository allowlist
scan-once entrypoint
ProjectPushFrame import requirement
Copilot advisory-only policy
publication review required
publication disabled by default
```

The patch is stdlib-only and performs no runtime startup, GitHub call, SQL
mutation, or Qdrant mutation.
