# Human-readable artifact identity — 0287-r7-r15-r2-r3

## Decision

An artifact has two complementary identities:

- a readable display/Actions name describing the Issue and content kind;
- an immutable typed reference and digest used for authority, correlation and replay.

The readable name never replaces `artifact_ref`, manifest hashes or SQL authority.

## Actions naming

`autodoc-i<issue>-<title-slug>--<kind>-v<schema-version>`

Examples:

- `autodoc-i42-validation-chaine-github-autodoc--authoritative-request-v1`
- `autodoc-i42-validation-chaine-github-autodoc--copilot-advisory-v2`
- `autodoc-i42-validation-chaine-github-autodoc--run-manifest-v1`

The legacy fixed names remain accepted by local consumers for historical runs.

## Boundaries

- request remains authoritative;
- Copilot remains consultative;
- manifest remains the digest/correlation evidence;
- the identity index is packaged beside the manifest;
- no Scheduler, SQL, Qdrant or OpenVINO behavior changes.
