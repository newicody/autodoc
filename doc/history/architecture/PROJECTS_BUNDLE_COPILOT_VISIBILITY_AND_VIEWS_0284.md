# Projects bundle Copilot visibility and views — 0284-r1-r4

## Ownership

```text
newicody/autodoc
└── templates/github/projects-repository/   source bundle only
                     │ controlled copy
                     ▼
newicody/projects
├── ProjectV2 fields and views
├── installation adapters
└── active Actions workflow
```

No ProjectV2 view manager is installed in Autodoc runtime modules or tools.

## Publication path

```text
GitHub Actions producer
→ authoritative request + advisory + manifest artifacts
→ local operator/laboratory validation
→ 0281 controlled Issue comment publication
→ copied Projects adapter projects latest Copilot fields
```

The workflow producer cannot invoke either publication step. Both remote
operations require explicit operator decisions and plan-digest confirmation.

## Authority

```text
Authoritative:
  GitHub request
  local operator decision
  server result

Consultative read-model:
  Copilot status
  Copilot summary
  suggested route
  confidence
  advisory artifact/cycle references
```

The Copilot field adapter is forbidden from writing `Résumé` and `Serveur`.

## View model

One research remains one primary card. Current fields provide a compact latest
state while append-only Issue comments preserve detailed history. The
`Connaissances serveur` view is separate from `Résultats`; visibility does not
imply ingestion into SQL or projection into Qdrant.
