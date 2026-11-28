# Changelog — Phase 5.16 — GitHub projection design

## Added

- `doc/GITHUB_PROJECTION_DESIGN.md`
- `doc/docs/architecture/context/40_github_projection_design.dot`

## Changed

- `doc/docs/architecture/00_global.dot`
  - ajoute le nœud `GitHubProjectionDesign` lié à `SourceCandidateStore`, `GitHubProject` et `GitHubFeedback`.
- `doc/docs/architecture/context/39_source_candidate_storage_report.dot`
  - relie la navigation vers la phase 5.16.

## Boundaries

- Pas d'API GitHub.
- Pas de token.
- Pas de réseau.
- Pas de polling.
- Pas de serveur/daemon.
- Pas de Qdrant.
- Pas de LLM.
- Pas d'appel OpenVINO.

## Dependencies

Aucune dépendance hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.16 formalise une projection GitHub future documentaire sans nouvelle règle de programmation.
```
