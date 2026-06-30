# Changelog — Phase 4.18-r2 — Source Candidate dans l'architecture globale

## Objectif

Intégrer explicitement la couche future `GitHub Project Orchestrator / SourceCandidate` dans le graphe général `doc/docs/architecture/00_global.dot`.

La Phase 4.18-r1 documentait déjà la couche dans des graphes dédiés, mais elle ne rendait pas encore cette brique visible depuis la carte globale du système.

## Modifié

- `doc/docs/architecture/00_global.dot`
  - ajout du layer futur `Layer 11 — Remote Work Intake future` ;
  - ajout des nœuds `GitHubProject`, `GitHubAction`, `CopilotMetadata`, `SourceCandidate`, `LocalAuthority`, `GitHubFeedback` ;
  - ajout des flux conceptuels : issue/push/ticket -> artifact -> SourceCandidate -> source locale autoritative -> projection GitHub ;
  - liens DOT vers `integrations/90_github_project_orchestrator.svg` et `integrations/91_source_candidate_lifecycle.svg`.
- `doc/docs/architecture/integrations/90_github_project_orchestrator.dot`
  - ajout d'un lien de navigation vers `../00_global.svg`.
- `doc/docs/architecture/integrations/91_source_candidate_lifecycle.dot`
  - ajout d'un lien de navigation vers `../00_global.svg`.

## Décision

La couche est visible dans l'architecture générale, mais reste future et documentaire.

Elle ne branche pas encore :

- l'API GitHub ;
- un token ;
- un polling réseau ;
- Copilot comme dépendance obligatoire ;
- le Scheduler ;
- Qdrant ;
- un backend LLM.

## Règle maintenue

GitHub reste une surface de pilotage et de synchronisation. La source autoritative enrichie reste sur le serveur local.

```text
GitHub Project / Issue / Push / Artifact
-> SourceCandidate
-> serveur local autoritatif
-> enrichissement / validation / fusion contexte
-> projection contrôlée vers GitHub
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 4.18-r2 intègre une couche future dans le graphe global sans ajouter de code runtime ni de dépendance externe.
```
